import os
import requests
import time
import fal_client
from dotenv import load_dotenv

class FalVideoGenerator:
    def __init__(self):
        load_dotenv()
        self.api_key = os.environ.get("FAL_API_KEY")
        if not self.api_key:
            raise ValueError("FAL_API_KEY environment variable is not set. Please set it in your .env file or environment.")
        fal_client.api_key = self.api_key

    def on_queue_update(self, update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                print(log["message"])

    def generate_video(self, prompt, image_path, output_path):
        print(f"Starting video generation for {output_path}...")

        # Upload the image to FAL's server
        image_url = fal_client.upload_file(image_path)
        print(f"Image uploaded successfully. URL: {image_url}")


        # Create generation with duration and aspect ratio
        result = fal_client.subscribe(
            "fal-ai/runway-gen3/turbo/image-to-video",
            arguments={
                "prompt": prompt,
                "image_url": image_url,
                "duration": "5",  # Set duration to 5 seconds
                "ratio": "9:16"  # Set aspect ratio to 9:16
            },
            with_logs=True,
            on_queue_update=self.on_queue_update,
        )
        print(f"Generation completed. Result: {result}")

        # Get video URL from the completed generation
        video_url = result.get('video', {}).get('url')
        if not video_url:
            raise Exception(f"Video URL not found in the generation response for {output_path}")

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
    generator = FalVideoGenerator()
    generator.generate_video(
        prompt="A bunny eating a carrot in the field.",
        image_path="path/to/your/image.jpg",
        output_path="bunny_video.mp4"
    )
