# File: src/main.py

import time
import threading
import logging
import yaml
import os
import sys

# Debugging: Print working and script directories, and check config.yaml existence
print(f"Working directory: {os.getcwd()}")
print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
config_path_debug = '/home/volumio/Quadifyclean/config.yaml'
print(f"Does config.yaml exist? {os.path.isfile(config_path_debug)}")

# Importing components from the src directory
from display.display_manager import DisplayManager
from display.clock import Clock
from display.playback_manager import PlaybackManager
from managers.mode_manager import ModeManager
from managers.manager_factory import ManagerFactory
from controls.rotary_control import RotaryControl
from network.volumio_listener import VolumioListener
from hardware.buttonsleds import ButtonsLEDController
from handlers.state_handler import StateHandler

def load_config(config_path='/config.yaml'):
    abs_path = os.path.abspath(config_path)
    print(f"Attempting to load config from: {abs_path}")
    print(f"Does the file exist? {os.path.isfile(config_path)}")  # Debug line
    config = {}
    if os.path.isfile(config_path):
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            logging.debug(f"Configuration loaded from {config_path}.")
        except yaml.YAMLError as e:
            logging.error(f"Error loading config file {config_path}: {e}")
    else:
        logging.warning(f"Config file {config_path} not found. Using default configuration.")
    return config

def main():
    # 1. Set up logging
    logging.basicConfig(
        level=logging.INFO,  # Changed from DEBUG to INFO to reduce verbosity
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger("Main")

    # 2. Suppress logging from third-party libraries
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('socketio').setLevel(logging.WARNING)
    logging.getLogger('engineio').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('blinker').setLevel(logging.WARNING)
    logging.getLogger('transitions').setLevel(logging.WARNING)

    # 3. Load configuration
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, '..', 'config.yaml')
    config_path = os.path.abspath(config_path)  # Ensure it's an absolute path
    print(f"Using config file path: {config_path}")
    config = load_config(config_path)

    # 4. Extract and pass display configuration to DisplayManager
    display_config = config.get('display', {})
    
    # Debugging: Print the display config being passed
    print("Display Config being passed to DisplayManager:", display_config)
    logging.debug(f"Display Config being passed to DisplayManager: {display_config}")

    print("Step 1: Initializing DisplayManager...")
    display_manager = DisplayManager(display_config)
    print("Step 1 complete: DisplayManager initialized.")

    # 5. Display startup logo and loading animation
    logo_path = os.path.join(script_dir, 'assets/images/logo.bmp')
    loading_gif_path = os.path.join(script_dir, 'assets/images/Loading.gif')

    print("Step 2: Displaying logo and loading animation...")
    display_manager.display_image(logo_path, resize=True)
    time.sleep(2)
    display_manager.display_image(loading_gif_path, resize=True, timeout=2)
    print("Step 2 complete: Displaying startup visuals.")

    # 6. Initialize VolumioListener
    volumio_config = config.get('volumio', {})
    volumio_host = volumio_config.get('host', 'localhost')
    volumio_port = volumio_config.get('port', 3000)

    print("Step 3: Initializing VolumioListener...")
    volumio_listener = VolumioListener(host=volumio_host, port=volumio_port)
    print("Step 3 complete: VolumioListener initialized.")

    # 7. Initialize Clock
    print("Step 4: Initializing Clock...")
    clock = Clock(display_manager, display_config)  # Pass display_config if needed
    print("Step 4 complete: Clock initialized.")

    # 8. Initialize PlaybackManager
    print("Step 5: Initializing PlaybackManager...")
    playback_manager = PlaybackManager(display_manager, volumio_listener, mode_manager=None)  # Ensure arguments match __init__
    print("Step 5 complete: PlaybackManager initialized.")

    # 9. Initialize ManagerFactory with DisplayManager and VolumioListener
    print("Step 6: Initializing ManagerFactory...")
    manager_factory = ManagerFactory(display_manager, volumio_listener, mode_manager=None)  # ModeManager will be set later
    print("Step 6 complete: ManagerFactory initialized.")

    # 10. Initialize other managers using ManagerFactory
    print("Step 7: Creating other managers...")
    menu_manager = manager_factory.create_menu_manager()
    playlist_manager = manager_factory.create_playlist_manager()
    radio_manager = manager_factory.create_radio_manager()
    tidal_manager = manager_factory.create_tidal_manager()
    qobuz_manager = manager_factory.create_qobuz_manager()
    print("Step 7 complete: Other managers created.")

    # 11. Initialize ModeManager with all managers
    print("Step 8: Initializing ModeManager...")
    mode_manager = ModeManager(
        display_manager=display_manager,
        clock=clock,
        playback_manager=playback_manager,
        menu_manager=menu_manager,
        playlist_manager=playlist_manager,
        radio_manager=radio_manager,
        tidal_manager=tidal_manager,
        qobuz_manager=qobuz_manager
    )
    print("Step 8 complete: ModeManager initialized.")

    # 12. Assign ModeManager to VolumioListener and other managers
    print("Step 9: Assigning ModeManager to managers...")
    volumio_listener.mode_manager = mode_manager
    playback_manager.mode_manager = mode_manager
    menu_manager.mode_manager = mode_manager
    playlist_manager.mode_manager = mode_manager
    radio_manager.mode_manager = mode_manager
    tidal_manager.mode_manager = mode_manager
    qobuz_manager.mode_manager = mode_manager
    print("Step 9 complete: ModeManager assigned.")

    # 13. Connect to Volumio after assigning ModeManager
    print("Step 10: Connecting to Volumio...")
    volumio_listener.connect()
    print("Step 10 complete: Connected to Volumio.")

    # 14. Initialize StateHandler
    print("Step 11: Initializing StateHandler...")
    state_handler = StateHandler(volumio_listener, mode_manager)
    print("Step 11 complete: StateHandler initialized.")

    # 15. Initialize ButtonsLEDController
    print("Step 12: Initializing ButtonsLEDController...")
    buttons_leds = ButtonsLEDController(
        volumio_listener=volumio_listener,
        config_path=config_path
    )
    buttons_leds.start()
    print("Step 12 complete: ButtonsLEDController started.")

    # 16. Define RotaryControl callbacks
    def on_rotate(direction):
        current_mode = mode_manager.get_mode()
        logger.debug(f"Rotary rotated: {'RIGHT' if direction == 1 else 'LEFT'} in mode {current_mode}.")
        if current_mode == 'menu':
            menu_manager.scroll_selection(direction)
        elif current_mode == 'webradio':
            radio_manager.scroll_selection(direction)
        elif current_mode == 'playlist':
            playlist_manager.scroll_selection(direction)
        elif current_mode == 'tidal':
            tidal_manager.scroll_selection(direction)
        elif current_mode == 'qobuz':
            qobuz_manager.scroll_selection(direction)
        elif current_mode == 'playback':
            volume_change = 5 * direction  # Adjust volume by 5 units per rotation
            playback_manager.adjust_volume(volume_change)

    def on_button_press():
        current_mode = mode_manager.get_mode()
        logger.debug(f"Button pressed in mode {current_mode}.")
        if current_mode == 'clock':
            mode_manager.to_menu()
        elif current_mode == 'menu':
            menu_manager.select_item()
        elif current_mode in ['webradio', 'playlist', 'favourites', 'tidal', 'qobuz']:
            pass
        elif current_mode == 'playback':
            playback_manager.toggle_play_pause()

    # 17. Initialize RotaryControl
    print("Step 13: Initializing RotaryControl...")
    rotary_control = RotaryControl(
        config_path=config_path,
        rotation_callback=on_rotate,
        button_callback=on_button_press
    )
    print("Step 13 complete: RotaryControl initialized.")

    # 18. Start RotaryControl GPIO event detection in a separate thread
    print("Step 14: Starting RotaryControl GPIO event detection...")
    rotary_thread = threading.Thread(target=rotary_control.setup_gpio, daemon=True)
    rotary_thread.start()
    print("Step 14 complete: RotaryControl GPIO event detection started.")

    # 19. Wait until VolumioListener is connected
    logger.info("Waiting for Volumio to connect...")
    while not volumio_listener.is_connected:
        time.sleep(1)
        logger.debug("Still waiting for Volumio to connect...")

    # 20. Set initial mode to Clock
    print("Step 15: Setting initial mode to Clock...")
    mode_manager.to_clock()
    print("Step 15 complete: Initial mode set to Clock.")

    # 21. Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down Quadify...")
    finally:
        # 22. Clean up resources
        buttons_leds.stop()
        rotary_control.stop()
        volumio_listener.stop_listener()
        display_manager.clear_screen()
        logger.info("Quadify has been shut down gracefully.")

if __name__ == "__main__":
    main()
