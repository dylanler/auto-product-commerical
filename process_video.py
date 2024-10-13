import os
import json
from moviepy.editor import VideoFileClip

def process_metadata():
    b_roll_metadata_dir = 'b_roll_metadata'
    b_roll_dir = 'b_roll_cut'

    # Iterate through JSON files in b_roll_metadata directory
    for filename in os.listdir(b_roll_metadata_dir):
        if filename.endswith('_metadata.json'):
            # Extract video name from filename
            video_name = filename.replace('_metadata.json', '')

            # Get corresponding video file path
            video_path = os.path.join(b_roll_dir, f"{video_name}.mp4")

            # Get video duration using moviepy
            video = VideoFileClip(video_path)
            duration = video.duration
            video.close()

            # Read existing JSON data
            json_path = os.path.join(b_roll_metadata_dir, filename)
            with open(json_path, 'r') as f:
                data = json.load(f)

            # Create a new dictionary with video_name as the first key
            updated_data = {
                'video_name': video_name,
                **data,
                'video_duration_length': duration
            }

            # Write updated JSON data back to file
            with open(json_path, 'w') as f:
                json.dump(updated_data, f, indent=2)

            print(f"Updated {filename} with video duration: {duration} and video name: {video_name}")

if __name__ == "__main__":
    process_metadata()
