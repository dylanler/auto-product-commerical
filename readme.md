# Auto Product Commercial Generator

This application automates the process of creating product commercials by leveraging AI-generated content and user-provided assets.

## Features

1. **LoRA Model Training**: Train custom LoRA models using your own image datasets.
2. **AI Image Generation**: Generate product images using trained LoRA models.
3. **Video Generation**: Create dynamic product videos from generated images.
4. **B-roll Integration**: Upload and incorporate B-roll footage into your commercials.
5. **AI Music Generation**: Generate background music for your commercials using AI.
6. **Video Stitching**: Combine product videos, B-roll footage, and music into a final commercial.

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/auto-product-commercial.git
   cd auto-product-commercial
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the root directory and add the following:
   ```
   FAL_API_KEY=your_fal_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

## Usage

1. Run the Gradio app:
   ```
   python app.py
   ```

2. Open your web browser and navigate to the local URL provided by Gradio (usually `http://127.0.0.1:7860`).

3. Follow the steps in the UI to:
   - Train a LoRA model
   - Generate images using the trained model
   - Create product videos
   - Upload B-roll footage
   - Generate background music
   - Stitch everything together into a final commercial

## Components

- `app.py`: Main application file containing the Gradio interface and core logic.
- `edit_picture.py`: Image processing utilities.
- `flux.py`: FluxImageGenerator for image generation.
- `runway.py`: FalVideoGenerator for video generation.
- `suno.py`: SongGenerator for AI music generation.
- `fal_train_lora.py`: LoraTrainer for custom LoRA model training.
- `fal_lora_inference.py`: FalLoraInference for generating images with trained LoRA models.

## Dependencies

- gradio
- Pillow
- moviepy
- numpy
- anthropic
- (other dependencies as listed in requirements.txt)

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.