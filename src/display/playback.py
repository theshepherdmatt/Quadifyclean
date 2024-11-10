import time
import threading
import requests
from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import spi
from luma.oled.device import ssd1322
import socketio
import os
from io import BytesIO


class WebRadio:
    def __init__(self, device, alt_font, alt_font_medium, local_album_art_path="/home/volumio/Quadifyclean/src/assets/images/webradio.bmp"):
        self.device = device
        self.alt_font = alt_font
        self.alt_font_medium = alt_font_medium
        self.local_album_art_path = local_album_art_path  # Local fallback image path

        # Load the local BMP fallback album art once during initialization
        try:
            self.default_album_art = Image.open(self.local_album_art_path).resize((40, 40)).convert("RGBA")
        except IOError:
            print("Local BMP album art not found. Please check the path.")
            self.default_album_art = None

    def draw(self, draw, data, base_image):
        # Determine if bitrate is available
        bitrate = data.get("bitrate", "")

        # Set position for the "Webradio" label based on bitrate availability
        webradio_y_position = 15 if bitrate else 25  # Move down if no bitrate

        # Draw the "Webradio" label at the calculated position
        draw.text((self.device.width // 2, webradio_y_position), "Webradio", font=self.alt_font_medium, fill="white", anchor="mm")

        # Display bitrate if available
        if bitrate:
            draw.text((self.device.width // 2, 35), bitrate, font=self.alt_font, fill="white", anchor="mm")

        # Attempt to load album art from URL
        album_art_url = data.get("albumart")
        album_art = None

        if album_art_url:
            try:
                response = requests.get(album_art_url)
                # Check if response contains image data
                if response.headers["Content-Type"].startswith("image"):
                    album_art = Image.open(BytesIO(response.content)).resize((60, 60)).convert("RGBA")
                else:
                    print("Album art URL did not return an image.")
                    
            except requests.RequestException:
                print("Could not load album art (network error).")
            except (PIL.UnidentifiedImageError, IOError):
                print("Could not load album art (unsupported format).")
        
        # Use the local BMP fallback if URL fetching fails
        if album_art is None and self.default_album_art:
            album_art = self.default_album_art

        # Paste album art on display if available
        if album_art:
            base_image.paste(album_art, (190, -4), album_art)


class Playback:
    def __init__(self, device, state, mode_manager, host='localhost', port=3000):
        self.device = device
        self.state = state
        self.mode_manager = mode_manager
        self.host = host
        self.port = port
        self.running = False
        self.VOL_API_URL = "http://localhost:3000/api/v1/getState"
        self.previous_service = None
        self.socketIO = socketio.Client(logger=True, engineio_logger=True)
        self.socketIO.connect(f'http://{self.host}:{self.port}', namespaces=['/'])
        
        font_path = "/home/volumio/Quadifyclean/src/assets/fonts/DSEG7Classic-Light.ttf"
        alt_font_path = "/home/volumio/Quadifyclean/src/assets/fonts/OpenSans-Regular.ttf"
        try:
            self.large_font = ImageFont.truetype(font_path, 45)
            self.alt_font_medium = ImageFont.truetype(alt_font_path, 18)
            self.alt_font = ImageFont.truetype(alt_font_path, 12)
        except IOError:
            print("Font file not found. Please check the font paths.")
            exit()

        self.icons = {}
        services = ["favourites", "nas", "playlists", "qobuz", "tidal", "webradio", "mpd", "default"]
        icon_dir = "/home/volumio/Quadifyclean/src/assets/images"
        for service in services:
            try:
                icon_path = os.path.join(icon_dir, f"{service}.bmp")
                self.icons[service] = Image.open(icon_path).convert("RGB").resize((40, 40))
            except IOError:
                print(f"Icon for {service} not found. Please check the path.")

        self.webradio = WebRadio(self.device, self.alt_font, self.alt_font_medium)

    def get_volumio_data(self):
        try:
            response = requests.get(self.VOL_API_URL)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to connect to Volumio. Status code: {response.status_code}")
        except requests.RequestException as e:
            print(f"Error fetching data from Volumio: {e}")
        return None

    def get_text_dimensions(self, text, font):
        bbox = font.getbbox(text)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return width, height

    def draw_display(self, data):
        current_service = data.get("service", "default").lower()
        
        # Clear the display if the service has changed
        if current_service != self.previous_service:
            self.device.clear()
            self.previous_service = current_service

        # Create an image to draw on
        image = Image.new("RGB", (self.device.width, self.device.height), "black")
        draw = ImageDraw.Draw(image)

        # Draw volume indicator
        volume = max(0, min(int(data.get("volume", 0)), 100))
        filled_squares = round((volume / 100) * 6)
        square_size = 4
        row_spacing = 4
        padding_bottom = 12
        columns = [8, 28]

        for x in columns:
            for row in range(6):
                y = self.device.height - padding_bottom - ((row + 1) * (square_size + row_spacing))
                if row < filled_squares:
                    draw.rectangle([x, y, x + square_size, y + square_size], fill="white")
                else:
                    draw.rectangle([x, y, x + square_size, y + square_size], outline="white")

        # Draw specific content based on service type
        if current_service == "webradio":
            # Use WebRadio class to handle web radio specific display
            self.webradio.draw(draw, data, image)
        else:
            # Display sample rate and bit depth for other services
            sample_rate = data.get("samplerate", "0 KHz")
            sample_rate_value, sample_rate_unit = sample_rate.split() if ' ' in sample_rate else (sample_rate, "")

            try:
                sample_rate_value = str(int(float(sample_rate_value)))
            except ValueError:
                sample_rate_value = "0"

            # Position sample rate in the center
            sample_rate_width, _ = self.get_text_dimensions(sample_rate_value, self.large_font)
            sample_rate_x = self.device.width / 2 - sample_rate_width / 2
            sample_rate_y = 26
            unit_x = sample_rate_x + sample_rate_width - 25
            unit_y = sample_rate_y + 19

            # Draw text for sample rate and unit
            draw.text((sample_rate_x, sample_rate_y), sample_rate_value, font=self.large_font, fill="white", anchor="mm")
            draw.text((unit_x, unit_y), sample_rate_unit, font=self.alt_font, fill="white", anchor="lm")

            # Display audio format and bit depth
            audio_format = data.get("trackType", "Unknown")
            bitdepth = data.get("bitdepth") or "N/A"
            format_bitdepth_text = f"{audio_format}/{bitdepth}"
            draw.text((210, 45), format_bitdepth_text, font=self.alt_font, fill="white", anchor="mm")

            # Display the icon based on service type
            icon = self.icons.get(current_service, self.icons["default"])
            image.paste(icon, (185, 0))

        # Display the final image on the OLED screen
        self.device.display(image)

    def start(self):
        if not self.running:
            self.running = True
            self.update_thread = threading.Thread(target=self.update_display)
            self.update_thread.start()
            print("Playback mode started.")

    def stop(self):
        if self.running:
            self.running = False
            if self.update_thread:
                self.update_thread.join()
            if self.mode_manager:
                self.mode_manager.clear_screen()
            print("Playback mode stopped and screen cleared.")

    def update_display(self):
        while self.running:
            data = self.get_volumio_data()
            if data:
                self.draw_display(data)
            else:
                print("No data received from Volumio.")
            time.sleep(1)


    def toggle_play_pause(self):
        # Emit the play/pause command to Volumio
        print("Toggling play/pause")
        self.socketIO.emit('toggle')
