import time
from src.display.display_manager import DisplayManager
from PIL import ImageDraw

# Configuration dictionary with fonts and display settings
config = {
    'fonts': {
        'default': {
            'path': '/home/volumio/Quadifyclean/src/assets/fonts/OpenSans-Regular.ttf',
            'size': 18
        },
        'playback_large': {
            'path': '/home/volumio/Quadifyclean/src/assets/fonts/DSEG7Classic-Light.ttf',
            'size': 45
        },
        'playback_medium': {
            'path': '/home/volumio/Quadifyclean/src/assets/fonts/OpenSans-Regular.ttf',
            'size': 18
        },
    },
    'display': {
        'logo_path': '/home/volumio/Quadifyclean/src/assets/images/logo.bmp'
    }
}

# Initialize the DisplayManager with the configuration
display_manager = DisplayManager(config=config)

# Test 1: Display the logo image for 2 seconds, then clear
print("Test 1: Displaying logo image.")
display_manager.show_logo()
time.sleep(2)
display_manager.clear_screen()
print("Screen cleared after logo display.\n")

# Test 2: Display a custom image and resize to fit screen, then clear
print("Test 2: Displaying custom image.")
image_path = "/home/volumio/Quadifyclean/src/assets/images/tidal.bmp"
display_manager.display_image(image_path, resize=True)
time.sleep(2)
display_manager.clear_screen()
print("Screen cleared after custom image display.\n")

# Test 3: Display text at various positions and sizes, then clear
print("Test 3: Displaying text.")
display_manager.display_text("Hello, World!", (10, 10), font_key='default')
time.sleep(2)
display_manager.clear_screen()

display_manager.display_text("Large Text Test", (10, 30), font_key='playback_large')
time.sleep(2)
display_manager.clear_screen()
print("Screen cleared after text display.\n")

# Test 4: Draw custom shapes (lines, rectangles, circles) and clear
def custom_drawing(draw):
    draw.rectangle([0, 0, 50, 50], outline="white", fill="black")
    draw.line([0, 0, 50, 50], fill="white", width=2)
    draw.ellipse([20, 20, 60, 60], outline="white", fill="black")
    draw.text((70, 30), "Shapes Test", font=display_manager.fonts['default'], fill="white")

print("Test 4: Drawing custom shapes.")
display_manager.draw_custom(custom_drawing)
time.sleep(2)
display_manager.clear_screen()
print("Screen cleared after custom shapes display.\n")

# Test 5: Startup sequence
print("Test 5: Testing startup sequence.")
display_manager.show_logo()
time.sleep(2)  # Allow time for logo to display
display_manager.clear_screen()
print("Startup sequence complete.\n")

# Test 6: Volume bar display using draw_custom
def draw_volume_bars_test(draw):
    volume = 75  # Example volume level (75%)
    filled_squares = round((volume / 100) * 6)
    square_size = 4
    row_spacing = 4
    padding_bottom = 12
    columns = [8, 28]

    for x in columns:
        for row in range(6):
            y = display_manager.oled.height - padding_bottom - ((row + 1) * (square_size + row_spacing))
            if row < filled_squares:
                draw.rectangle([x, y, x + square_size, y + square_size], fill="white")
            else:
                draw.rectangle([x, y, x + square_size, y + square_size], outline="white")

print("Test 6: Displaying volume bars.")
display_manager.draw_custom(draw_volume_bars_test)
time.sleep(2)
display_manager.clear_screen()
print("Screen cleared after volume bars display.\n")

# Test 7: Display multiple lines of text for readability testing
print("Test 7: Displaying multiple lines of text.")
display_manager.display_text("Line 1", (10, 10), font_key='default')
display_manager.display_text("Line 2", (10, 30), font_key='default')
display_manager.display_text("Line 3", (10, 50), font_key='default')
time.sleep(2)
display_manager.clear_screen()
print("Screen cleared after multiple lines of text display.\n")

# Final screen clear to ensure display is clean before ending test
display_manager.clear_screen()
print("All tests complete. Final screen clear executed.\n")
