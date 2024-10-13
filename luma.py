import os
import requests
import time
from lumaai import LumaAI
from dotenv import load_dotenv

class LumaVideoGenerator:
    def __init__(self):
        load_dotenv()
        self.client = LumaAI(
            auth_token=os.environ.get("LUMA_API_TOKEN"),
        )

    def generate_video(self, prompt, image_url, output_path):
        # Create generation
        print(f"Starting video generation for {output_path}...")
        generation = self.client.generations.create(
            prompt=prompt,
            loop=True,
            keyframes={
                "frame0": {
                    "type": "image",
                    "url": image_url
                }
            }
        )
        print(f"Generation started with ID: {generation.id}")

        # Wait for generation to complete
        while True:
            generation = self.client.generations.get(generation.id)
            if generation.state == "completed":
                print(f"Video generation completed successfully for {output_path}!")
                break
            elif generation.state == "failed":
                raise Exception(f"Generation failed for {output_path}: {generation.failure_reason}")
            else:
                print(f"Generation in progress for {output_path}... Current state: {generation.state}")
            time.sleep(10)  # Wait for 10 seconds before checking again

        # Get video URL from the completed generation
        print(f"Retrieving video URL for {output_path}...")
        if hasattr(generation, 'assets') and isinstance(generation.assets, dict):
            video_url = generation.assets.get("video")
        elif hasattr(generation, 'assets') and hasattr(generation.assets, 'video'):
            video_url = generation.assets.video
        else:
            raise Exception(f"Video URL not found in the generation response for {output_path}")

        if not video_url:
            raise Exception(f"Video URL is empty for {output_path}")

        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Download the video
        print(f"Downloading video to {output_path}...")
        response = requests.get(video_url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0

        with open(output_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=block_size):
                file.write(chunk)
                downloaded += len(chunk)
                progress = (downloaded / total_size) * 100
                print(f"Download progress for {output_path}: {progress:.2f}%", end='\r')
        
        print(f"\nVideo generated and saved to {output_path}")

# Example usage
if __name__ == "__main__":
    generator = LumaVideoGenerator()
    generator.generate_video(
        prompt="Low-angle shot of a majestic tiger prowling through a snowy landscape, leaving paw prints on the white blanket",
        image_url="https://storage.cdn-luma.com/dream_machine/7e4fe07f-1dfd-4921-bc97-4bcf5adea39a/video_0_thumb.jpg",
        output_path="tiger_video.mp4"
    ) 