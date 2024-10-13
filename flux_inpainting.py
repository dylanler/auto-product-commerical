import fal_client
import os
import requests
from PIL import Image
import io
from dotenv import load_dotenv
from datetime import datetime
import numpy as np

# Load environment variables from .env file
load_dotenv()

class FluxInpainting:
    def __init__(self):
        self.prompt = "product commercial photoshoot vibrant colorful background"
        self.output_dir = "image_inpainted"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set the FAL API key
        fal_client.api_key = os.getenv('FAL_API_KEY')

    def on_queue_update(self, update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                print(log["message"])

    def generate_mask(self, image_path):
        # Open the image and convert to RGBA
        img = Image.open(image_path).convert("RGBA")
        
        # Create a mask from the alpha channel
        alpha = np.array(img.split()[-1])
        mask = Image.fromarray((alpha == 0).astype(np.uint8) * 255)
        
        # Save the mask
        mask_path = os.path.join(self.output_dir, f"generated_mask_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        mask.save(mask_path)
        
        return mask_path

    def inpaint(self, image_path):
        # Generate mask from the input image
        mask_path = self.generate_mask(image_path)

        # Upload image and mask files
        image_url = fal_client.upload_file(image_path)
        mask_url = fal_client.upload_file(mask_path)

        result = fal_client.subscribe(
            "fal-ai/flux-lora/inpainting",
            arguments={
                "prompt": self.prompt,
                "image_url": image_url,
                "mask_url": mask_url
            },
            with_logs=True,
            on_queue_update=self.on_queue_update,
        )
        
        # Save the inpainted image
        if 'images' in result and len(result['images']) > 0:
            image_url = result['images'][0]['url']
            image_data = requests.get(image_url).content
            img = Image.open(io.BytesIO(image_data))
            output_path = os.path.join(self.output_dir, f"inpainted_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
            img.save(output_path)
            print(f"Inpainted image saved to: {output_path}")
        else:
            print("No image found in the API response.")
        
        return result


inpainter = FluxInpainting()
result = inpainter.inpaint("product_img/input5_processed.png")
print(result)
