import os
import random
from moviepy.editor import VideoFileClip

def cut_b_roll_videos():
    # Define input and output directories
    input_dir = 'b_roll'
    output_dir = 'b_roll_cut'

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Iterate through all mp4 files in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith('.mp4'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)

            # Load the video
            video = VideoFileClip(input_path)

            # Generate a random duration between 2 and 5 seconds
            cut_duration = random.uniform(2, 5)

            # Cut the video
            cut_video = video.subclip(0, cut_duration)

            # Write the cut video to the output directory
            cut_video.write_videofile(output_path, codec='libx264')

            # Close the video objects
            video.close()
            cut_video.close()

    print("All videos have been processed and saved in the 'b_roll_cut' directory.")

if __name__ == "__main__":
    cut_b_roll_videos()

