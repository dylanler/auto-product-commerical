import os
import replicate
from datetime import datetime
from dotenv import load_dotenv
import requests
from urllib.parse import urlparse
from img_bucket import GCPImageUploader

class ImageGenerator:
    def __init__(self):
        load_dotenv()
        self.replicate_api_token = os.getenv('REPLICATE_API_TOKEN')
        if not self.replicate_api_token:
            raise ValueError("REPLICATE_API_TOKEN is not set in the environment variables")
        self.client = replicate.Client(api_token=self.replicate_api_token)
        self.uploader = GCPImageUploader()

    def generate_image(self, mask, input_image, prompt):
        mask_data = self._prepare_image(mask, "mask")
        input_data = self._prepare_image(input_image, "input")

        output = replicate.run(
            "zsxkib/flux-dev-inpainting:ca8350ff748d56b3ebbd5a12bd3436c2214262a4ff8619de9890ecc41751a008",
            input={
                "mask": mask_data,
                "image": input_data,
                "prompt": prompt,
                "strength": 0.85,
                "output_format": "png",
                "output_quality": 80,
                "num_inference_steps": 25
            }
        )

        output_list = list(output)
        if output_list:
            image_url = output_list[0]
            print(f"Generated image URL: {image_url}")
            return self._download_and_save_image(image_url)
        else:
            print("No output was generated")
            return None

    def _prepare_image(self, image_source, image_type):
        if self._is_url(image_source):
            return image_source
        elif os.path.isfile(image_source):
            with open(image_source, "rb") as f:
                return f.read()
        else:
            raise ValueError(f"Invalid {image_type} source. Must be a URL or a file path.")

    def _is_url(self, string):
        try:
            result = urlparse(string)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def _download_and_save_image(self, image_url):
        response = requests.get(image_url)
        if response.status_code == 200:
            current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gen_image_{current_datetime}.png"
            
            os.makedirs('generated_img', exist_ok=True)
            file_path = os.path.join('generated_img', filename)
            
            with open(file_path, 'wb') as file:
                file.write(response.content)
            
            print(f"Image saved as {file_path}")
            return file_path
        else:
            print("Failed to download the image")
            return None

# Example usage:
if __name__ == "__main__":
    generator = ImageGenerator()
    mask_path = "mask_img/output_mask.png"
    input_image_path = "product_img/input.png"
    prompt = "sports shoes with a colorful background for a product commercial, vibrant colors, high quality, 4k high definition"
    
    output_path = generator.generate_image(mask_path, input_image_path, prompt)
    if output_path:
        print(f"Image generated and saved at: {output_path}")
    else:
        print("Image generation failed")
