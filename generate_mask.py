from PIL import Image
import numpy as np
import os

class MaskGenerator:
    def __init__(self, alpha_threshold=128):
        """
        Initialize the MaskGenerator with a given alpha threshold.

        Args:
            alpha_threshold (int): Threshold for alpha channel to consider as foreground.
        """
        self.alpha_threshold = alpha_threshold

    def generate_mask(self, input_image):
        """
        Generates a binary mask from a PIL Image object with a transparent background.
        Foreground (object) will be black, and background will be white.

        Args:
            input_image (PIL.Image): Input PIL Image object.

        Returns:
            PIL.Image: The generated mask as a PIL Image object.
        """
        # Ensure the image is in RGBA mode
        img = input_image.convert('RGBA')
        print(f"Image mode: {img.mode}")

        # Convert image to numpy array
        img_array = np.array(img)
        print(f"Image shape: {img_array.shape}")

        # Check if alpha channel is present
        if img_array.shape[2] < 4:
            raise ValueError("Input image does not have an alpha channel.")

        # Create a mask where alpha channel > alpha_threshold
        alpha_mask = img_array[:, :, 3] > self.alpha_threshold
        print(f"Foreground pixels: {np.sum(alpha_mask)} out of {alpha_mask.size}")

        # Initialize mask with white background
        mask = np.full((img_array.shape[0], img_array.shape[1]), 255, dtype=np.uint8)

        # Set foreground pixels to black
        mask[alpha_mask] = 0

        # Create and return the mask image
        return Image.fromarray(mask)

if __name__ == "__main__":
    import argparse

    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Generate a binary mask from a PNG image with transparency.")
    parser.add_argument('input_image', nargs='?', default='product_img/input.png', help="Path to the input PNG image.")
    parser.add_argument('output_mask', nargs='?', default='mask_img/output_mask.png', help="Path to save the output mask image.")
    parser.add_argument('--threshold', type=int, default=128, help="Alpha threshold for masking (0-255). Default is 128.")

    args = parser.parse_args()

    # Check if input file exists
    if not os.path.isfile(args.input_image):
        raise FileNotFoundError(f"Input file {args.input_image} does not exist.")

    # Create MaskGenerator instance
    mask_generator = MaskGenerator(alpha_threshold=args.threshold)

    # Open the input image
    input_img = Image.open(args.input_image)

    # Generate the mask
    mask = mask_generator.generate_mask(input_img)

    # Save the mask
    mask.save(args.output_mask)
    print(f"Mask generated and saved to {args.output_mask}")
