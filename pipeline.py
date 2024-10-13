from flux import FluxImageGenerator
from datetime import datetime
from generate_mask import MaskGenerator
from generate_image import ImageGenerator
from PIL import Image
import os
from img_bucket import GCPImageUploader  # Import the GCPImageUploader class
from stitch_image import ImageStitcher  # Import the ImageStitcher class
from luma import LumaVideoGenerator  # Import the LumaVideoGenerator class

def generate_commercial_background():
    generator = FluxImageGenerator()
    prompt = "Vibrant and colorful abstract background for a commercial, dynamic and eye-catching"
    origin_image = "product_img/input5.png"
    
    # Generate a unique filename with datetime
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"generated_img/gen_image_{current_time}.png"
    
    try:
        generated_path = generator.generate_image(prompt, origin_image, output_path)
        print(f"Commercial background generated and saved to: {generated_path}")
        return generated_path, origin_image
    except Exception as e:
        print(f"Error generating background: {str(e)}")
        return None, None

def generate_product_mask():
    mask_generator = MaskGenerator()
    input_path = "product_img/input2.png"
    uploader = GCPImageUploader()  # Use GCPImageUploader instead of ImgurUploader

    # Generate a unique filename with datetime
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"mask_img/output_mask_{current_time}.png"
    
    try:
        # Open the input image
        input_img = Image.open(input_path)
        
        # Generate the mask
        mask = mask_generator.generate_mask(input_img)
        
        # Save the mask
        mask.save(output_path)
        print(f"Product mask generated and saved to: {output_path}")

        # Upload mask to GCP
        mask_url = uploader.upload_image(output_path)
        print(f"Mask uploaded to GCP: {mask_url}")

        # Upload input image to GCP
        input_url = uploader.upload_image(input_path)
        print(f"Input image uploaded to GCP: {input_url}")

        # Return the URL strings
        return mask_url, input_url
    except Exception as e:
        print(f"Error generating product mask or uploading images: {str(e)}")
        return None, None

def generate_final_image(mask_url, input_url):
    generator = ImageGenerator()
    prompt = "colorful background for a product commercial, vibrant colors, high quality, 4k high definition"
    
    try:
        # Check if mask_url and input_url are valid strings
        if not isinstance(mask_url, str) or not isinstance(input_url, str):
            raise ValueError("Invalid mask_url or input_url")

        output_path = generator.generate_image(mask_url, input_url, prompt)
        if output_path:
            print(f"Final image generated and saved at: {output_path}")
        else:
            print("Final image generation failed")
    except Exception as e:
        print(f"Error generating final image: {str(e)}")

def stitch_images(background_path, overlay_path):
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"stitch_img/stitched_img_{current_time}.png"
    
    try:
        stitcher = ImageStitcher(background_path, overlay_path)
        stitcher.save_final_image(output_path)
        print(f"Stitched image saved to: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error stitching images: {str(e)}")
        return None

def upload_to_gcp(image_path):
    uploader = GCPImageUploader()
    try:
        image_url = uploader.upload_image(image_path)
        print(f"Image uploaded to GCP: {image_url}")
        return image_url
    except Exception as e:
        print(f"Error uploading image to GCP: {str(e)}")
        return None

def generate_video(image_url):
    generator = LumaVideoGenerator()
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"generated_vid/generated_vid_{current_time}.mp4"
    prompt = "Vibrant and dynamic commercial showcasing the product"
    
    try:
        generator.generate_video(prompt, image_url, output_path)
        print(f"Video generated and saved to: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error generating video: {str(e)}")
        return None

if __name__ == "__main__":
    generated_path, origin_image = generate_commercial_background()
    if generated_path and origin_image:
        stitched_image_path = stitch_images(generated_path, origin_image)
        if stitched_image_path:
            print(f"Final stitched image: {stitched_image_path}")
            
            # Upload stitched image to GCP
            gcp_image_url = upload_to_gcp(stitched_image_path)
            if gcp_image_url:
                # Generate video using Luma
                video_path = generate_video(gcp_image_url)
                if video_path:
                    print(f"Final video generated: {video_path}")

    # Uncomment the following lines if you want to run the mask generation and final image generation
    # mask_url, input_url = generate_product_mask()
    # if mask_url and input_url:
    #     generate_final_image(mask_url, input_url)

