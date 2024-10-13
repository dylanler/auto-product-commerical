import os
from datetime import datetime
import gradio as gr
from PIL import Image
from edit_picture import ImageProcessor
from flux import FluxImageGenerator
from luma import LumaVideoGenerator
from img_bucket import GCPImageUploader
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, ColorClip, CompositeVideoClip
import concurrent.futures
from functools import partial
import random
from suno import SongGenerator

# Initialize generators and uploader
flux_generator = FluxImageGenerator()
luma_generator = LumaVideoGenerator()
gcp_uploader = GCPImageUploader()

# Initialize song generator
song_generator = SongGenerator()

# Create directories if they don't exist
def create_directories():
    directories = ['temp_uploaded', 'overlaid_img', 'background_img', 'gen_video', 'processed_img']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Get timestamped filename
def get_timestamped_filename(prefix, extension):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"

# New function to get a unique filename
def get_unique_filename(directory, prefix, extension):
    base_filename = get_timestamped_filename(prefix, extension)
    full_path = os.path.join(directory, base_filename)
    counter = 1
    while os.path.exists(full_path):
        new_filename = f"{prefix}_{counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
        full_path = os.path.join(directory, new_filename)
        counter += 1
    return full_path

def generate_background(style, idx):
    style_prompts = {
        "colorful": "colorful vibrant pattern background art high definition",
        "cyberpunk": "modern neon lights pattern background art high definition",
        "floral": "floral print pattern background art high definition",
        "minimalist": "clean minimalist geometric pattern background art high definition",
        "vintage": "retro vintage texture pattern background art high definition",
        # New style prompts
        "abstract": "abstract expressionist painting pattern background art high definition",
        "futuristic": "sleek futuristic sci-fi pattern background art high definition",
        "nature": "serene natural landscape pattern background art high definition",
        "industrial": "gritty industrial urban pattern background art high definition",
        "pop_art": "bold pop art style pattern background art high definition"
    }
    background_path = get_unique_filename('background_img', f"background_{idx}", "png")
    flux_generator.generate_image(style_prompts[style], output_path=background_path)
    return background_path

def process_images(images, style):
    processed_images = []
    overlaid_images = []
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Generate backgrounds in parallel
        background_futures = [executor.submit(generate_background, style, idx) for idx in range(len(images))]
        background_paths = [future.result() for future in concurrent.futures.as_completed(background_futures)]
    
    for idx, (image, background_path) in enumerate(zip(images, background_paths)):
        if image is not None:
            background = Image.open(background_path)
            
            # Save uploaded image temporarily
            temp_path = get_unique_filename('temp_uploaded', f"temp_upload_{idx}", "png")
            image.save(temp_path)
            
            # Process image
            processor = ImageProcessor(temp_path)
            processor.process_image()
            processed_path = processor.output_path
            
            # Save processed image in processed_img directory
            processed_save_path = get_unique_filename('processed_img', f"processed_{idx}", "png")
            Image.open(processed_path).save(processed_save_path)
            
            processed_images.append(processed_save_path)
            
            # Resize background to match processed image dimensions
            processed = Image.open(processed_path)
            background = background.resize((processed.width, processed.height), Image.LANCZOS)
            
            print(f"Processed image dimensions: {processed.width}x{processed.height}")
            print(f"Resized background dimensions: {background.width}x{background.height}")
            
            combined = background.copy()
            
            # Paste the processed image onto the background
            combined.paste(processed, (0, 0), processed)
            
            overlaid_path = get_unique_filename('overlaid_img', f"overlaid_{idx}", "png")
            combined.save(overlaid_path)
            overlaid_images.append(overlaid_path)
            
            # Clean up temporary files
            os.remove(temp_path)
    
    return overlaid_images, processed_images

def generate_video(overlaid_images):
    output_videos = []
    
    # Create a new directory with timestamp for this batch of videos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_dir = f'gen_video_{timestamp}'
    os.makedirs(video_dir, exist_ok=True)
    
    for idx, image_path in enumerate(overlaid_images):
        if image_path is not None:
            # Upload the image to GCP and get the URL
            image_url = gcp_uploader.upload_image(image_path)
            print(f"Uploaded image {idx + 1} URL: {image_url}")

            # Generate video for each image
            output_path = get_unique_filename(video_dir, f"output_video_{idx + random.randint(1, 1000)}", "mp4")
            luma_generator.generate_video(
                prompt='''
                Product comercial shoot with interesting and captivating product shots 
                The product is rotated and the camera does a zoom and pan to entice the viewer to buy the product
                ''',
                image_url=image_url,  # Use the uploaded image URL
                output_path=output_path
            )
            output_videos.append(output_path)
        else:
            output_videos.append(None)
    
    # Pad the output with None values to always return 5 items
    return output_videos + [None] * (5 - len(output_videos))

def stitch_videos_with_audio(video_paths, audio_path):
    # Filter out None values from video_paths
    valid_video_paths = [path for path in video_paths if path is not None]
    
    if not valid_video_paths:
        return None
    
    video_clips = [VideoFileClip(path) for path in valid_video_paths]
    
    # Add the ending video and resize it
    ending_video = VideoFileClip("generated_vid/simplycodes_ending.mp4")
    
    # Get the dimensions of the first video clip
    target_width, target_height = video_clips[0].w, video_clips[0].h
    
    # Calculate the scaling factor
    scale_factor = min(target_width / ending_video.w, target_height / ending_video.h)
    
    # Calculate new dimensions
    new_width = int(ending_video.w * scale_factor)
    new_height = int(ending_video.h * scale_factor)
    
    # Resize the ending video
    ending_video_resized = ending_video.resize(newsize=(new_width, new_height))
    
    # Create a black background of the target size
    bg = ColorClip(size=(target_width, target_height), color=(0,0,0))
    bg = bg.set_duration(ending_video_resized.duration)
    
    # Composite the resized video onto the center of the background
    x_offset = (target_width - new_width) // 2
    y_offset = (target_height - new_height) // 2
    ending_video_final = CompositeVideoClip([bg, ending_video_resized.set_position((x_offset, y_offset))])
    
    # Add the final ending video to the list of clips
    video_clips.append(ending_video_final)

    final_clip = concatenate_videoclips(video_clips)
    
    if audio_path:
        audio_clip = AudioFileClip(audio_path)
        # Trim audio to match video duration if necessary
        if audio_clip.duration > final_clip.duration:
            audio_clip = audio_clip.subclip(0, final_clip.duration)
        final_clip = final_clip.set_audio(audio_clip)
    
    output_path = get_unique_filename('gen_video', 'final_stitched_video', 'mp4')
    final_clip.write_videofile(output_path)
    
    # Close all clips to free up resources
    for clip in video_clips:
        clip.close()
    if audio_path:
        audio_clip.close()
    final_clip.close()
    ending_video.close()
    
    return output_path

def generate_song(prompt):
    try:
        print(f"Generating song with prompt: {prompt}")
        mp3_files = song_generator.generate_song(prompt)
        if mp3_files:
            return mp3_files[0]  # Return the first generated song
    except Exception as e:
        print(f"Error generating song: {str(e)}")
    return None

def app_function(image1, image2, image3, image4, image5, style):
    create_directories()  # Ensure directories exist
    images = [img for img in [image1, image2, image3, image4, image5] if img is not None]
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(process_images, images, style)
        overlaid_images, processed_images = future.result()
    
    # Pad the outputs with None values to always return 5 items
    overlaid_output = overlaid_images + [None] * (5 - len(overlaid_images))
    
    # Return only the overlaid images
    return overlaid_output

def generate_videos_parallel(*overlaid_images):
    valid_images = [img for img in overlaid_images if img is not None]
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(generate_video, [img]) for img in valid_images]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # Flatten the results list and pad with None values to always return 5 items
    flattened_results = [item for sublist in results for item in sublist if item is not None]
    return flattened_results + [None] * (5 - len(flattened_results))

with gr.Blocks() as demo:
    gr.Markdown("# Auto Product Commercial")
    
    with gr.Row():
        image_inputs = [gr.Image(type="pil", label=f"Upload Image {i+1}") for i in range(5)]
    
    style = gr.Dropdown(choices=["colorful", "cyberpunk", "floral", "minimalist", "vintage", "abstract", "futuristic", "nature", "industrial", "pop_art"], label="Select Style")
    
    submit_btn = gr.Button("Process Images")
    
    with gr.Row():
        output_overlaid = [gr.Image(type="filepath", label=f"Overlaid Image {i+1}") for i in range(5)]
    
    submit_btn.click(
        app_function,
        inputs=image_inputs + [style],
        outputs=output_overlaid
    )
    
    video_btn = gr.Button("Generate Videos")
    with gr.Row():
        video_outputs = [gr.Video(label=f"Generated Video {i+1}") for i in range(5)]

    # Replace audio_input with text input for song prompt
    song_prompt = gr.Textbox(label="Enter song prompt")
    generate_song_btn = gr.Button("Generate Song")
    audio_output = gr.Audio(label="Generated Song", type="filepath")

    generate_song_btn.click(
        generate_song,
        inputs=[song_prompt],
        outputs=[audio_output]
    )
    
    video_btn.click(
        generate_videos_parallel,
        inputs=output_overlaid,
        outputs=video_outputs
    )
    
    stitch_btn = gr.Button("Stitch Video Together")
    final_video_output = gr.Video(label="Final Stitched Video")
    
    stitch_btn.click(
        lambda *args: stitch_videos_with_audio(args[:-1], args[-1]),
        inputs=video_outputs + [audio_output],
        outputs=final_video_output
    )

# make the app live
demo.launch()