import time
import threading
import logging 
import atexit
import socketio
from datetime import datetime
from luma.core.interface.serial import spi
from luma.oled.device import ssd1322
from PIL import Image, ImageDraw, ImageSequence
import sys
import requests
import RPi.GPIO as GPIO
from playback import Playback
from clock import Clock
from volumio_listener import VolumioListener
from rotary import RotaryControl
from mode_Manager import ModeManager
from menus import PlaylistManager, RadioManager
from menu_manager import MenuManager
from buttonsleds import ButtonsLEDController

GPIO.setwarnings(False)

volumioIO = socketio.Client(logger=True, engineio_logger=True)
volumioIO.connect('http://localhost:3000', namespaces=['/'])

LOADING_GIF_PATH = "/home/volumio/Quadify/Loading.gif"

# Timers
LOGO_DISPLAY_TIME = 5
last_button_press_time = 0

# Initialize OLED display
def initialize_display():
    print("Initializing OLED display...")
    serial = spi(device=0, port=0)
    device = ssd1322(serial, rotate=2)
    print("OLED display initialized successfully.")
    return device

# Initialize ButtonsLEDController
controller = ButtonsLEDController(volumioIO=volumioIO)

# Start button checking and Volumio status update in separate threads
button_thread = threading.Thread(target=controller.check_buttons_and_update_leds, daemon=True)
status_thread = threading.Thread(target=controller.start_status_update_loop, daemon=True)

button_thread.start()
status_thread.start()

device = initialize_display()
clock = Clock(device)

# Instantiate ModeManager first without other dependencies
mode_manager = ModeManager(device, clock)

# Initialize VolumioListener with the handle_state_change callback
listener = VolumioListener(
    on_state_change_callback=mode_manager.process_state_change,
    oled=device,
    clock=clock,
    mode_manager=mode_manager,
)

# Initialize other components with listener and ModeManager references
menu_manager = MenuManager(device, listener, mode_manager)
playlist_manager = PlaylistManager(device, listener, mode_manager)
radio_manager = RadioManager(device, listener, mode_manager)

# Now that all components are initialized, set ModeManager dependencies
mode_manager.menu_manager = menu_manager
mode_manager.playlist_manager = playlist_manager
mode_manager.radio_manager = radio_manager
#mode_manager.rotary_control = rotary_control


# Define managers dictionary
managers = {
    "Playlists": playlist_manager,
    "Radio": radio_manager,
    # Future managers can be added here, e.g.,
}

# Define get_volumio_state
def get_volumio_state():
    """Helper function to fetch the current Volumio state."""
    try:
        response = requests.get("http://localhost:3000/api/v1/getState")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get Volumio state. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error fetching data from Volumio: {e}")
    return None

def handle_state_change(state):
    """Sends state changes to ModeManager and lets it handle mode decisions."""
    mode_manager.process_state_change(state)

def is_correct_time():
    """Checks if the system time has been updated to a realistic time."""
    # Assume time is set correctly if the year is after 2022
    current_year = datetime.now().year
    return current_year > 2022

def show_loading_gif(device, gif_path=LOADING_GIF_PATH, display_duration=0.1):
    """Displays a loading GIF frame by frame until network time updates."""
    try:
        print(f"Attempting to open loading GIF from {gif_path}")
        with Image.open(gif_path) as img:
            while not is_correct_time():
                print("Displaying loading GIF frames...")
                for frame in ImageSequence.Iterator(img):
                    frame_resized = frame.convert(device.mode).resize((device.width, device.height))
                    device.display(frame_resized)
                    time.sleep(display_duration)  # Controls GIF speed
    except IOError:
        print("Loading GIF file not found or could not be opened. Please check the path.")
        sys.exit(1)

# Display the boot logo
def display_boot_logo(device):
    logo_path = "/home/volumio/Quadify/logo.bmp"
    try:
        logo = Image.open(logo_path).convert(device.mode).resize((device.width, device.height))
        device.display(logo)
        print("Boot logo displayed.")
        time.sleep(LOGO_DISPLAY_TIME)  # Display the logo for the specified time

        # Clear the logo before loading animation
        mode_manager.clear_screen()

        # After logo, display loading animation until time syncs
        print("Starting loading animation until network time updates...")
        show_loading_gif(device)
        print("Network time synchronized. Switching to clock.")

    except IOError:
        print("Logo file not found. Please check the path to the logo image.")
        sys.exit(1)

display_boot_logo(device)

mode_manager.set_mode("clock")
print("Set initial mode to clock and started clock display.")

# Fetch and handle the initial Volumio state
initial_state = get_volumio_state()  # Ensure initial_state is defined
if initial_state:
    # Process the initial Volumio state using ModeManager
    mode_manager.process_state_change(initial_state)
else:
    # If unable to fetch state, default to clock mode
    print("Unable to fetch Volumio state. Defaulting to clock mode.")
    mode_manager.set_mode("clock")
    clock.start()

# Define a function to update the OLED screen based on the current mode
def screen_update(current_mode):
    global device

    if device is None:
        print("OLED instance not initialized. Cannot update screen.")
        return

    # Clear the OLED first
    mode_manager.clear_screen()

    # Now, display the new mode
    if current_mode == "menu":
        print("Displaying menu.")
        menu_manager.start_menu_mode()
    elif current_mode == "clock":
        print("Switching to Clock Mode")
        clock.start()
    elif current_mode == "playback":
        print("Switching to Playback Mode")
        if mode_manager.playback:
            mode_manager.playback.start()
    elif current_mode == "webradio":
        print("Switching to Webradio Mode")
        if mode_manager.radio_manager:
            mode_manager.radio_manager.start_radio_mode()  # Explicitly call the function to start RadioManager mode
    elif current_mode == "playlist":
        print("Switching to Playlist Mode")
        if mode_manager.playlist_manager:
            mode_manager.playlist_manager.start_playlist_mode()  # Explicitly call the function to start PlaylistManager mode
    else:
        print("Switching to Unknown Mode")

    
# Register screen_update as a callback in ModeManager
mode_manager.add_on_mode_change_callback(screen_update)

# Define adjust_volume function
def adjust_volume(volume_change):
    """Adjusts the volume by the specified amount (+/-)."""
    try:
        # Get the current volume to adjust it
        response = requests.get("http://localhost:3000/api/v1/getState")
        if response.status_code == 200:
            data = response.json()
            current_volume = data.get("volume", 0)
            if current_volume is None:
                current_volume = 0  # Set to 0 if current volume is not available

            # Calculate the new volume, clamping it between 0 and 100
            new_volume = max(0, min(100, current_volume + volume_change))
            
            # Make a request to Volumio to update the volume
            requests.get(f"http://localhost:3000/api/v1/commands/?cmd=volume&volume={new_volume}")
            print(f"Volume adjusted to: {new_volume}%")
        else:
            print(f"Failed to get current volume from Volumio. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error adjusting volume: {e}")

# Create instance of RotaryControl
rotary_control = RotaryControl(
    clk_pin=13,
    dt_pin=5,
    sw_pin=6,
    rotation_callback=mode_manager.handle_rotation,
    button_callback=mode_manager.handle_button_press,
    mode_manager=mode_manager
)

mode_manager.rotary_control = rotary_control

# Initialize the last_status attribute for handle_state_change
handle_state_change.last_status = None

# Initialize PlaylistManager using the listener instance
#playlist_manager = PlaylistManager(device, listener, mode_manager)
#print("PlaylistManager initialized successfully.")

def start_listener():
    listener_thread = threading.Thread(target=listener.connect)
    listener_thread.daemon = True
    listener_thread.start()
    print("Volumio listener started in a separate thread.")

# Start listener thread
start_listener()

# Register cleanup to GPIO
def cleanup():
    GPIO.cleanup()

atexit.register(cleanup)

# Main loop
if __name__ == "__main__":
    print("OLED display setup complete.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTerminating gracefully...")
        clock.stop()
        mode_manager.clear_screen()
        rotary_control.stop()
