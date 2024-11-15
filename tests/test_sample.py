# test_playback_display.py

import time
import logging
from src.display.display_manager import DisplayManager
from src.display.playback_manager import PlaybackManager
from src.network.volumio_listener import VolumioListener
from yaml import safe_load

# Load configuration for DisplayManager
with open('config.yaml', 'r') as config_file:
    config = safe_load(config_file)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PlaybackTest")

def main():
    # Initialize DisplayManager with configuration
    display_manager = DisplayManager(config)
    logger.info("DisplayManager initialized.")

    # Initialize VolumioListener to connect to Volumio's WebSocket API
    volumio_listener = VolumioListener(host='localhost', port=3000)
    logger.info("VolumioListener initialized.")

    # Initialize PlaybackManager with DisplayManager and VolumioListener
    playback_manager = PlaybackManager(display_manager=display_manager,
                                       volumio_listener=volumio_listener,
                                       mode_manager=None)  # Assuming mode_manager isn't needed for this test

    logger.info("PlaybackManager initialized.")
    
    # Start listening to playback events
    playback_manager.start_mode()
    logger.info("Playback mode started.")

    try:
        # Keep the script running to listen and update the display
        while True:
            # Refresh the display based on any updates from Volumio
            playback_manager.display_current_track()
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Test script interrupted. Stopping...")
        playback_manager.stop_mode()
        display_manager.clear_screen()
        logger.info("Playback mode stopped and screen cleared.")

if __name__ == "__main__":
    main()
