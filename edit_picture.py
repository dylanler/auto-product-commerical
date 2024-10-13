import os
from PIL import Image
from rembg import remove

class ImageProcessor:
    def __init__(self, input_path):
        self.input_path = input_path
        self.output_path = self._generate_output_path()

    def _generate_output_path(self):
        directory, filename = os.path.split(self.input_path)
        name, _ = os.path.splitext(filename)
        return os.path.join(directory, f"{name}_processed.png")

    def process_image(self):
        # Open the input image
        with Image.open(self.input_path) as img:
            # Remove background
            img_no_bg = remove(img)

            # Create a 9:16 transparent canvas
            canvas_width = 1080  # You can adjust this value
            canvas_height = int(canvas_width * 16 / 9)
            canvas = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))

            # Resize the image to fit on the canvas
            img_aspect = img_no_bg.width / img_no_bg.height
            canvas_aspect = canvas_width / canvas_height

            if img_aspect > canvas_aspect:
                # Image is wider, fit to width
                new_width = canvas_width
                new_height = int(new_width / img_aspect)
            else:
                # Image is taller, fit to height
                new_height = canvas_height
                new_width = int(new_height * img_aspect)

            img_resized = img_no_bg.resize((new_width, new_height), Image.LANCZOS)

            # Calculate position to paste the image (center)
            paste_x = (canvas_width - new_width) // 2
            paste_y = (canvas_height - new_height) // 2

            # Paste the resized image onto the canvas
            canvas.paste(img_resized, (paste_x, paste_y), img_resized)

            # Save the result
            canvas.save(self.output_path, 'PNG')

        print(f"Processed image saved as: {self.output_path}")

# Example usage
if __name__ == "__main__":
    input_image = "product_img/input5.png"
    processor = ImageProcessor(input_image)
    processor.process_image()