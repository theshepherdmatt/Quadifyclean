# src/main.py
import time
import threading
import atexit
from dependency_injector.wiring import inject, Provide
from containers import Container
from src.commands.play_command import PlayCommand
from src.commands.pause_command import PauseCommand
from src.commands.volume_up_command import VolumeUpCommand
from src.commands.volume_down_command import VolumeDownCommand
from src.commands.command_invoker import CommandInvoker
from src.network.volumio_listener import VolumioListener
from src.utils.service_locator import ServiceLocator
from src.utils.config_loader import load_config
from luma.oled.device import ssd1322
from luma.core.interface.serial import spi
import RPi.GPIO as GPIO
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,  # Change to INFO or WARNING in production
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("quadifyclean.log"),
            logging.StreamHandler()
        ]
    )

@inject
def main(
    container: Container = Provide[Container],
    command_invoker: CommandInvoker = Provide[Container.command_invoker],
):
    # Setup logging
    setup_logging()
    logger = logging.getLogger('Main')
    logger.info("Starting Quadifyclean Application")

    # Load configuration
    container.config.from_yaml('config.yaml')

    # Initialize components
    oled = container.oled_device()
    display_manager = container.display_manager()
    volumio_listener = container.volumio_listener()
    mode_manager = container.mode_manager()
    menu_manager = container.menu_manager()
    playlist_manager = container.playlist_manager()
    radio_manager = container.radio_manager()
    tidal_manager = container.tidal_manager()
    qobuz_manager = container.qobuz_manager()
    playback_manager = container.playback()
    rotary_control = container.rotary_control()
    button_led_controller = container.button_led_controller()
    state_handler = container.state_handler()

    # Register Volumio state change handler
    def handle_volumio_state_change(state):
        mode_manager.process_state_change(state)

    volumio_listener.state_changed.connect(handle_volumio_state_change)

    # Register playlists received handler
    def handle_playlists_received(playlists):
        playlist_manager.update_playlists(playlists)

    volumio_listener.playlists_received.connect(handle_playlists_received)

    # Register webradio received handler
    def handle_webradio_received(stations):
        radio_manager.update_webradio_stations(stations)

    volumio_listener.webradio_received.connect(handle_webradio_received)

    # Register Tidal playlists received handler
    def handle_tidal_playlists_received(playlists):
        tidal_manager.update_tidal_playlists(playlists)

    volumio_listener.tidal_playlists_received.connect(handle_tidal_playlists_received)

    # Register Qobuz playlists received handler
    def handle_qobuz_playlists_received(playlists):
        qobuz_manager.update_qobuz_playlists(playlists)

    volumio_listener.qobuz_playlists_received.connect(handle_qobuz_playlists_received)

    # Register track changed handler
    def handle_track_changed(track_info):
        playback_manager.update_current_track(track_info)

    volumio_listener.track_changed.connect(handle_track_changed)

    # Define button press callback
    def on_button_press():
        current_mode = mode_manager.get_mode()
        logger.debug(f"Button pressed in mode: {current_mode}")
        if current_mode == "menu":
            menu_manager.select_item()
        elif current_mode == "playlist":
            playlist_manager.select_item()
        elif current_mode == "playback":
            playback_manager.toggle_play_pause()
        elif current_mode == "webradio":
            radio_manager.select_item()
        elif current_mode == "tidal":
            tidal_manager.select_item()
        elif current_mode == "qobuz":
            qobuz_manager.select_item()
        # Add more mode-specific button actions as needed

    # Define rotary encoder rotation callback
    def on_rotation(direction):
        current_mode = mode_manager.get_mode()
        logger.debug(f"Rotary turned {'Clockwise' if direction > 0 else 'Counterclockwise'} in mode: {current_mode}")
        if current_mode == "menu":
            menu_manager.scroll_selection(direction)
        elif current_mode == "playlist":
            playlist_manager.scroll_selection(direction)
        elif current_mode == "playback":
            # Example: Volume control
            if direction > 0:
                cmd = VolumeUpCommand(volumio_listener=volumio_listener, increment=5)
            else:
                cmd = VolumeDownCommand(volumio_listener=volumio_listener, decrement=5)
            command_invoker.execute_command(cmd)
        elif current_mode == "webradio":
            radio_manager.scroll_selection(direction)
        elif current_mode == "tidal":
            tidal_manager.scroll_selection(direction)
        elif current_mode == "qobuz":
            qobuz_manager.scroll_selection(direction)
        # Add more mode-specific rotation actions as needed

    # Wire callbacks to RotaryControl
    rotary_control.rotation_callback = on_rotation
    rotary_control.button_callback = on_button_press

    # Initialize and start state handler
    state_handler_instance = state_handler()
    state_handler_instance.register_listeners()

    # Initialize and start Volumio listener
    volumio_listener.connect()

    # Start LED controller in a separate thread
    def led_controller_thread():
        button_led_controller.start()
    
    threading.Thread(target=led_controller_thread, daemon=True).start()

    # Define cleanup function
    def cleanup():
        logger.info("Cleaning up resources...")
        GPIO.cleanup()
        rotary_control.stop()
        button_led_controller.stop()
        mode_manager.enter_clock()
        logger.info("Cleanup complete.")

    # Register cleanup to be called on exit
    atexit.register(cleanup)

    # Start the main loop
    try:
        logger.info("Quadifyclean is now running.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Exiting application.")
        cleanup()

if __name__ == "__main__":
    container = Container()
    container.wire(modules=[__name__])
    main()
