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
        level=logging.INFO,  # Adjust level as needed
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger = logging.getLogger("Main")

    # 2. Load configuration
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, '..', 'config.yaml')
    config = load_config(config_path)

    # 3. Initialize DisplayManager
    display_config = config.get('display', {})
    display_manager = DisplayManager(display_config)

    # 4. Initialize VolumioListener
    volumio_config = config.get('volumio', {})
    volumio_host = volumio_config.get('host', 'localhost')
    volumio_port = volumio_config.get('port', 3000)
    volumio_listener = VolumioListener(host=volumio_host, port=volumio_port)

    # 5. Initialize Clock
    clock = Clock(display_manager, display_config)

    # 6. Initialize ModeManager Early
    mode_manager = ModeManager(
        display_manager=display_manager,
        clock=clock,
        playback_manager=None,  # Placeholder, set later
        menu_manager=None,
        playlist_manager=None,
        radio_manager=None,
        tidal_manager=None,
        qobuz_manager=None
    )

    # 7. Initialize ManagerFactory
    manager_factory = ManagerFactory(display_manager, volumio_listener, mode_manager)

    # 8. Create Managers Using ManagerFactory
    menu_manager = manager_factory.create_menu_manager()
    playlist_manager = manager_factory.create_playlist_manager()
    radio_manager = manager_factory.create_radio_manager()
    tidal_manager = manager_factory.create_tidal_manager()
    qobuz_manager = manager_factory.create_qobuz_manager()

    # 9. Assign Managers to ModeManager
    mode_manager.playback_manager = PlaybackManager(display_manager, volumio_listener, mode_manager)
    mode_manager.menu_manager = menu_manager
    mode_manager.playlist_manager = playlist_manager
    mode_manager.radio_manager = radio_manager
    mode_manager.tidal_manager = tidal_manager
    mode_manager.qobuz_manager = qobuz_manager

    # 10. Assign ModeManager to VolumioListener
    volumio_listener.mode_manager = mode_manager

    # 11. Initialize ButtonsLEDController
    buttons_leds = ButtonsLEDController(volumio_listener=volumio_listener, config_path=config_path)

    # 12. Define RotaryControl Callbacks
    def on_rotate(direction):
        current_mode = mode_manager.get_mode()
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
            volume_change = 5 * direction
            mode_manager.playback_manager.adjust_volume(volume_change)

    def on_button_press():
        current_mode = mode_manager.get_mode()
        if current_mode == 'clock':
            mode_manager.to_menu()
        elif current_mode == 'menu':
            menu_manager.select_item()

    # 13. Initialize RotaryControl
    rotary_control = RotaryControl(
        config_path=config_path,
        rotation_callback=on_rotate,
        button_callback=on_button_press
    )

    # 14. Start RotaryControl Event Detection
    rotary_thread = threading.Thread(target=rotary_control.setup_gpio, daemon=True)
    rotary_thread.start()

    # 15. Wait Until VolumioListener is Connected
    logger.info("Waiting for Volumio to connect...")
    while not volumio_listener.is_connected:
        time.sleep(1)

    # 16. Set Initial Mode to Clock
    mode_manager.to_clock()

    # 17. Run the Main Application Loop
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down Quadify...")
    finally:
        buttons_leds.stop()
        rotary_control.stop()
        volumio_listener.stop_listener()
        display_manager.clear_screen()
        logger.info("Quadify has been shut down gracefully.")


if __name__ == "__main__":
    main()
