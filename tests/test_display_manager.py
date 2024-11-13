import time
from src.display.display_manager import DisplayManager

# Configuration dictionary for fonts and display
config = {
    'fonts': {
        'default': {
            'path': 'OpenSans-Regular.ttf',
            'size': 18
        }
    }
}

# Initialize the display manager
display_manager = DisplayManager(config=config)

# Display the logo image for 2 seconds
display_manager.display_image("/home/volumio/Quadifyclean/src/assets/images/logo.bmp", resize=True)
time.sleep(2)  # Show the logo for 2 seconds

# Clear the screen
display_manager.clear_screen()
print("Screen cleared")
