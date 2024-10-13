from PIL import Image

class ImageStitcher:
    def __init__(self, background_path, overlay_path):
        self.background = Image.open(background_path)
        self.overlay = Image.open(overlay_path).convert("RGBA")

    def stitch_images(self):
        # Resize the background to match the overlay size
        self.background = self.background.resize(self.overlay.size, Image.LANCZOS)

        # Paste the overlay image onto the background image
        self.background.paste(self.overlay, (0, 0), self.overlay)

        return self.background

    def save_final_image(self, output_path):
        final_image = self.stitch_images()
        final_image.save(output_path)

# Usage example
if __name__ == "__main__":
    background_path = "generated_img/gen_image_20240925_144845.png"
    overlay_path = "/Users/dylan/github/hackathon-project/product_img/input.png"
    output_path = "final_image.png"

    stitcher = ImageStitcher(background_path, overlay_path)
    stitcher.save_final_image(output_path)