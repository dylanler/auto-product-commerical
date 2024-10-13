import os
import time
import requests
from dotenv import load_dotenv
import sys
from PIL import Image

class FluxImageGenerator:
    def __init__(self):
        self.api_key = self._load_api_key()

    def _load_api_key(self):
        """Load the Replicate API key from the .env file."""
        load_dotenv()
        api_key = os.getenv('REPLICATE_API_TOKEN')
        if not api_key:
            raise ValueError("Error: REPLICATE_API_TOKEN not found in .env file.")
        return api_key

    def _create_prediction(self, prompt, origin_image=None, steps=25, guidance=3, interval=2, output_format="webp", output_quality=80, safety_tolerance=2):
        """Create a new prediction using the Replicate API with additional parameters."""
        url = "https://api.replicate.com/v1/models/black-forest-labs/flux-pro/predictions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": {
                "prompt": prompt,
                "steps": steps,
                "guidance": guidance,
                "interval": interval,
                "aspect_ratio": "9:16",  # Set the aspect ratio to 9:16 for phone wallpapers
                "output_format": output_format,
                "output_quality": output_quality,
                "safety_tolerance": safety_tolerance
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 201:
            raise RuntimeError(f"Error creating prediction: {response.status_code} - {response.text}")
        prediction = response.json()
        return prediction.get('urls', {}).get('get')

    def _poll_prediction(self, prediction_url):
        """Poll the prediction URL until the prediction is complete."""
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        while True:
            response = requests.get(prediction_url, headers=headers)
            if response.status_code != 200:
                raise RuntimeError(f"Error polling prediction: {response.status_code} - {response.text}")
            prediction = response.json()
            status = prediction.get('status')
            print(f"Prediction status: {status}")
            if status == "succeeded":
                return prediction.get('output')
            elif status in ["failed", "canceled"]:
                raise RuntimeError(f"Prediction {status}. {response.text}")
            time.sleep(5)

    def _download_image(self, image_url, output_path="output_image.png"):
        """Download the generated image from the provided URL."""
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"Image downloaded successfully and saved to {output_path}")
        else:
            raise RuntimeError(f"Error downloading image: {response.status_code} - {response.text}")

    def generate_image(self, prompt, origin_image=None, output_path="output_image.png"):
        """Generate an image based on the given prompt and origin image, and save it to the specified path."""
        print("Creating prediction...")
        prediction_url = self._create_prediction(prompt, origin_image)
        if not prediction_url:
            raise ValueError("Error: Prediction URL not found in the response.")

        print("Polling for prediction status...")
        output = self._poll_prediction(prediction_url)

        if isinstance(output, list):
            image_url = output[0]
        elif isinstance(output, str):
            image_url = output
        else:
            raise ValueError("Unexpected output format.")

        print(f"Downloading image from {image_url}...")
        self._download_image(image_url, output_path)
        return output_path

def main():
    if len(sys.argv) < 2:
        prompt = input("Enter your image prompt: ")
        origin_image = input("Enter the path to the origin image (optional, press Enter to skip): ") or None
    else:
        prompt = ' '.join(sys.argv[1:-1]) if len(sys.argv) > 2 else sys.argv[1]
        origin_image = sys.argv[-1] if len(sys.argv) > 2 and os.path.isfile(sys.argv[-1]) else None

    generator = FluxImageGenerator()
    try:
        output_path = generator.generate_image(prompt, origin_image)
        print(f"Image generated and saved to: {output_path}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()





