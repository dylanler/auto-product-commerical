import os
import json
from datetime import datetime
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv
import time
import typing_extensions as typing
import concurrent.futures
from moviepy.editor import VideoFileClip
from PIL import Image
import numpy as np

class VideoMetadata(typing.TypedDict):
    video_description: str
    objects_in_video: list[str]
    humans_in_video: list[str]
    fashion_aesthetics_of_humans: list[str]
    aesthetics_and_vibe_of_scene: str

class GeminiDescriber:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        self.video_model = genai.GenerativeModel(model_name="gemini-1.5-pro-002")
        self.image_model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        self.output_dir = None

    def describe_video(self, video_path: str) -> VideoMetadata:
        print(f"Uploading file...")
        video_file = genai.upload_file(path=video_path)
        print(f"Completed upload: {video_file.uri}")

        while video_file.state.name == "PROCESSING":
            print('.', end='', flush=True)
            time.sleep(10)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            raise ValueError(f"Video processing failed: {video_file.state.name}")

        prompt = '''
        Describe this video in detail.  
        Capture the camera movements, lighting, and any other details.
        Identify and label the objects in the video.
        If there are humans, describe their clothing, aesthetic, appearance, and actions.
        Output the aesthetics and vibe of the video.
        '''

        print("Making LLM inference request...")
        response = self.video_model.generate_content(
            [video_file, prompt],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=VideoMetadata
            ),
            request_options={"timeout": 600}
        )

        return response.text

    def describe_image(self, image: np.ndarray) -> str:
        # Convert numpy array to PIL Image
        pil_image = Image.fromarray(image)

        # Save the image to a temporary file
        temp_file = "temp_image.jpg"
        pil_image.save(temp_file)

        # Upload the image file
        image_file = genai.upload_file(path=temp_file)
        
        while image_file.state.name == "PROCESSING":
            print('.', end='', flush=True)
            time.sleep(10)
            image_file = genai.get_file(image_file.name)

        if image_file.state.name == "FAILED":
            raise ValueError(f"Image processing failed: {image_file.state.name}")

        prompt = "Describe this image in detail. Focus on the subject, composition, colors, and overall aesthetic. Give concise output."

        response = self.image_model.generate_content([image_file, prompt])

        # Remove the temporary file
        os.remove(temp_file)

        return response.text

    def describe_lora_outputs(self, lora_outputs: list[np.ndarray]) -> list[str]:
        descriptions = []
        for image in lora_outputs:
            if image is not None:
                description = self.describe_image(image)
                descriptions.append(description)
            else:
                descriptions.append(None)
        return descriptions

    def get_video_duration(self, video_path: str) -> float:
        with VideoFileClip(video_path) as clip:
            return clip.duration

    def save_metadata(self, metadata: str, video_name: str, video_path: str):
        if self.output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir = Path(f"video_metadata_{timestamp}")
            self.output_dir.mkdir(exist_ok=True)
        
        metadata_dict = json.loads(metadata)
        
        # Get video duration and add it to the metadata
        duration = self.get_video_duration(video_path)
        metadata_dict['video_duration_length'] = duration
        
        file_name = self.output_dir / f"{video_name}_metadata.json"
        with open(file_name, 'w') as f:
            json.dump(metadata_dict, f, indent=2)
        print(f"Metadata saved to {file_name}")

    def process_directory(self, directory_path: str, max_workers: int = 5):
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(f"video_metadata_{timestamp}")
        self.output_dir.mkdir(exist_ok=True)
        
        directory = Path(directory_path)
        video_files = list(directory.glob('*.mp4'))  # Adjust the extension if needed
        
        print(f"Found {len(video_files)} video files in {directory_path}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.process_single_video, video_file): video_file for video_file in video_files}
            
            for future in concurrent.futures.as_completed(futures):
                video_file = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"Error processing {video_file}: {str(e)}")

    def process_single_video(self, video_path: Path):
        print(f"Processing {video_path.name}...")
        metadata = self.describe_video(str(video_path))
        self.save_metadata(metadata, video_path.stem, str(video_path))
        print(f"Completed processing {video_path.name}")

    def process_directory_sequential(self, directory_path: str):
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(f"video_metadata_{timestamp}")
        self.output_dir.mkdir(exist_ok=True)
        
        directory = Path(directory_path)
        video_files = list(directory.glob('*.mp4'))  # Adjust the extension if needed
        
        print(f"Found {len(video_files)} video files in {directory_path}")
        
        for video_file in video_files:
            try:
                self.process_single_video(video_file)
            except Exception as e:
                print(f"Error processing {video_file}: {str(e)}")

def main():
    describer = GeminiDescriber()

    # For a single video
    # video_path = "gen_video_20241012_231941/output_video_759_20241012_231941.mp4"
    # metadata = describer.describe_video(video_path)
    # describer.save_metadata(metadata, Path(video_path).stem)

    # For a directory of videos (parallel)
    # directory_path = "b_roll"
    # describer.process_directory(directory_path)

    # For a directory of videos (sequential)
    directory_path = "b_roll"
    describer.process_directory_sequential(directory_path)

    # Example usage for describing LoRA outputs
    # Assuming lora_outputs is a list of numpy arrays representing images
    lora_outputs = [
        # ... your lora output images as numpy arrays ...
    ]
    image_descriptions = describer.describe_lora_outputs(lora_outputs)
    for i, description in enumerate(image_descriptions):
        if description:
            print(f"Description for LoRA output {i + 1}:")
            print(description)
            print()

if __name__ == "__main__":
    main()
