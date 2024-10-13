import os
from dotenv import load_dotenv
import pyimgur
import requests
import time

class ImgurUploader:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        # Get Imgur credentials from environment variables
        self.IMGUR_CLIENT_ID = os.getenv('IMGUR_CLIENT_ID')
        self.IMGUR_CLIENT_SECRET = os.getenv('IMGUR_CLIENT_SECRET')

        # Initialize Imgur client
        self.im = pyimgur.Imgur(self.IMGUR_CLIENT_ID)

    def upload_image(self, image_path):
        """
        Upload an image to Imgur and return the URL link.
        
        :param image_path: Path to the image file
        :return: Imgur URL link of the uploaded image
        """
        # Upload the image
        uploaded_image = self.im.upload_image(image_path, title="")
        
        # Convert the link to the desired format
        imgur_id = uploaded_image.link.split('/')[-1].split('.')[0]
        modified_link = f"https://imgur.com/{imgur_id}"
        
        print(f"Image uploaded. Link: {modified_link}")
        
        return self._verify_upload(modified_link)

    def _verify_upload(self, link):
        max_attempts = 10
        attempt = 0
        while attempt < max_attempts:
            try:
                # Request the link and get the redirected URL
                response = requests.get(link, timeout=5, allow_redirects=True)
                response.raise_for_status()
                
                # Return the final URL after redirects
                final_url = response.url
                print(f"Image verified successfully after {attempt + 1} attempts.")
                print(f"Final URL: {final_url}")
                time.sleep(1)
                return final_url
            except requests.exceptions.RequestException as e:
                # If unsuccessful, wait and try again
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if "429" in str(e):
                    print("Rate limit reached. Returning unverified link with a warning.")
                    return link, "WARNING: Link not verified due to rate limiting"
                time.sleep(2)
                attempt += 1
        
        # If max attempts reached, return the original link with a warning
        return link, "WARNING: Link not verified after multiple attempts"

# Example usage
if __name__ == "__main__":
    try:
        uploader = ImgurUploader()
        image_path = "product_img/input.png"  # Replace with your image path
        result = uploader.upload_image(image_path)
        if isinstance(result, tuple):
            imgur_link, warning = result
            print(f"Image uploaded. Imgur link: {imgur_link}")
            print(f"Warning: {warning}")
        else:
            imgur_link = result
            print(f"Image uploaded successfully. Imgur link: {imgur_link}")
    except Exception as e:
        print(f"Error: {str(e)}")
