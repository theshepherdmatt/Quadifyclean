from PIL import Image

def add_black_background_to_bmp(input_path, output_path, background_size=(100, 100)):
    """
    Adds a black background to an existing BMP image with potential white borders.
    
    Parameters:
    - input_path: Path to the original BMP file.
    - output_path: Path to save the new BMP with a black background.
    - background_size: Size of the background in pixels (width, height).
    """
    # Open the original BMP image
    original_image = Image.open(input_path)
    
    # Ensure the image is in RGB format
    if original_image.mode != "RGB":
        original_image = original_image.convert("RGB")
    
    # Create a black background image of the desired size
    background = Image.new("RGB", background_size, "black")
    
    # Center the original BMP on the black background
    position = (
        (background_size[0] - original_image.width) // 2,
        (background_size[1] - original_image.height) // 2
    )
    background.paste(original_image, position)

    # Save the output as a new BMP file
    background.save(output_path, "BMP")
    print(f"New BMP with black background saved at: {output_path}")

# Example usage
add_black_background_to_bmp("/home/volumio/Quadify/icons/mpd.bmp", "/home/volumio/Quadify/icons/mpd1.bmp")

