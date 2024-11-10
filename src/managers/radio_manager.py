from PIL import Image, ImageDraw, ImageFont

class RadioManager:
    WINDOW_SIZE = 5  # Number of lines to display at once

    def __init__(self, oled, volumio_listener, mode_manager):
        print("[Debug] Initializing RadioManager")
        # Initialize essential components
        self.oled = oled
        self.volumio_listener = volumio_listener
        self.mode_manager = mode_manager

        # Set up initial menu and display state
        self.current_menu = "categories"  # Start in the categories menu by default
        self.current_selection_index = 0
        self.window_start_index = 0  # Start index of the visible window
        self.categories = ["My Web Radios", "Popular Radios", "BBC Radios"]
        self.stations = []

        # Set up the font
        self.font_path = "/home/volumio/Quadifyclean/src/assets/fonts/OpenSans-Regular.ttf"
        try:
            self.font = ImageFont.truetype(self.font_path, 12)
        except IOError:
            print(f"Font file not found at {self.font_path}. Using default font.")
            self.font = ImageFont.load_default()

        # Register callback to update stations when fetched from Volumio
        self.volumio_listener.register_webradio_callback(self.update_stations)

        # Display the categories initially
        self.display_categories()
        print("[RadioManager] Initialized and displayed categories.")

        # Register mode change callback
        self.mode_manager.add_on_mode_change_callback(self.handle_mode_change)

    def start_radio_mode(self):
        print("[RadioManager] Entering radio mode and fetching categories.")
        self.current_selection_index = 0
        self.window_start_index = 0
        self.current_menu = "categories"
        self.mode_manager.current_mode = "webradio"
        self.display_categories()
        print("[RadioManager] Categories displayed. Waiting for user input.")

    def stop_mode(self):
        print("[RadioManager] Exiting radio mode and clearing display.")
        self.clear_display()

    def handle_mode_change(self, new_mode):
        print(f"[RadioManager] Mode change detected. New mode: {new_mode}")
        if new_mode == "webradio":
            self.start_radio_mode()
        elif new_mode != "webradio":
            self.stop_mode()

    def display_categories(self):
        print("[RadioManager] Displaying categories menu on OLED.")
        image = Image.new(self.oled.mode, (self.oled.width, self.oled.height), "black")
        draw = ImageDraw.Draw(image)

        visible_categories = self.get_visible_window(self.categories)
        y_offset = 0
        x_offset_arrow = 5
        x_offset_text = 20

        for i, category in enumerate(visible_categories):
            actual_index = self.window_start_index + i
            if actual_index == self.current_selection_index:
                draw.text((x_offset_arrow, y_offset), "->", font=self.font, fill="white")
                draw.text((x_offset_text, y_offset), category, font=self.font, fill="white")
            else:
                draw.text((x_offset_text, y_offset), category, font=self.font, fill="gray")
            y_offset += 15

        self.oled.display(image)
        print("[RadioManager] Categories displayed successfully.")

    def display_stations(self):
        if not self.stations:
            print("[RadioManager] No stations available to display.")
            self.display_no_stations_message()
            return

        print("[RadioManager] Displaying stations on OLED.")
        image = Image.new(self.oled.mode, (self.oled.width, self.oled.height), "black")
        draw = ImageDraw.Draw(image)

        visible_stations = self.get_visible_window([station['title'] for station in self.stations])
        y_offset = 0
        x_offset_arrow = 5
        x_offset_text = 20

        for i, station_title in enumerate(visible_stations):
            actual_index = self.window_start_index + i
            if actual_index == self.current_selection_index:
                draw.text((x_offset_arrow, y_offset), "->", font=self.font, fill="white")
                draw.text((x_offset_text, y_offset), station_title, font=self.font, fill="white")
            else:
                draw.text((x_offset_text, y_offset), station_title, font=self.font, fill="gray")
            y_offset += 15

        self.oled.display(image)
        print("[RadioManager] Stations displayed successfully.")

    def get_visible_window(self, items):
        """
        Determines the subset of items to display based on the current selection index.
        Ensures that the selected item is centered whenever possible.
        """
        total_items = len(items)
        half_window = self.WINDOW_SIZE // 2

        if total_items <= self.WINDOW_SIZE:
            self.window_start_index = 0
        else:
            if self.current_selection_index < half_window:
                self.window_start_index = 0
            elif self.current_selection_index > total_items - half_window - 1:
                self.window_start_index = total_items - self.WINDOW_SIZE
            else:
                self.window_start_index = self.current_selection_index - half_window

        # Ensure window_start_index is within bounds
        self.window_start_index = max(0, min(self.window_start_index, total_items - self.WINDOW_SIZE))

        end_index = self.window_start_index + self.WINDOW_SIZE
        return items[self.window_start_index:end_index]

    def update_stations(self, stations):
        """Update the list of available radio stations."""
        print(f"[RadioManager] Updating stations with received data.")

        # Update the stations list with new data
        self.stations = [
            {'title': station.get('title', 'Untitled').strip(), 'uri': station.get('uri', '').strip()}
            for station in stations
        ]

        # Debug output of stations received
        print(f"[Debug] Stations updated: {self.stations}")

        # Reset selection indices when new stations are loaded
        self.current_selection_index = 0
        self.window_start_index = 0

        # Display the stations if available, otherwise show 'No Stations Found' message
        if self.stations:
            self.display_stations()
        else:
            self.display_no_stations_message()

    def scroll_selection(self, direction):
        print(f"[RadioManager] Received scroll direction: {direction}")  # Debug: Verify direction

        if self.current_menu == "categories":
            options = self.categories
        else:
            options = [station['title'] for station in self.stations]

        if not options:
            print("[RadioManager] No options available to scroll.")
            return

        previous_index = self.current_selection_index

        # Ensure direction is an integer and handle scroll up/down correctly
        if isinstance(direction, int) and direction > 0:  # Scroll down
            if self.current_selection_index < len(options) - 1:
                self.current_selection_index += 1
        elif isinstance(direction, int) and direction < 0:  # Scroll up
            if self.current_selection_index > 0:
                self.current_selection_index -= 1
        else:
            print("[RadioManager] Invalid scroll direction provided.")
            return

        # Update the window based on the new selection
        self.get_visible_window(options)

        # Only update display if the index actually changed
        if previous_index != self.current_selection_index:
            print(f"[RadioManager] Scrolled to index: {self.current_selection_index}")
            if self.current_menu == "categories":
                self.display_categories()
            else:
                self.display_stations()
        else:
            print("[RadioManager] Reached the end/start of the list. Scroll input ignored.")

    def select_item(self):
        if self.current_menu == "categories":
            # Selecting a category
            selected_category = self.categories[self.current_selection_index]
            print(f"Selected radio category: {selected_category}")

            if selected_category == "My Web Radios":
                self.volumio_listener.fetch_webradio_stations('radio/myWebRadio')
            elif selected_category == "Popular Radios":
                self.volumio_listener.fetch_webradio_stations('radio/tunein/popular')
            elif selected_category == "BBC Radios":
                self.volumio_listener.fetch_webradio_stations('radio/bbc')
            else:
                print(f"[Warning] Unknown category selected: {selected_category}")

            # Move to stations menu without displaying yet
            self.current_menu = "stations"
            self.current_selection_index = 0
            self.window_start_index = 0
            print(f"[RadioManager] Switched to stations for category: {selected_category}")

        elif self.current_menu == "stations":
            # Selecting a station to play
            if not self.stations:
                print("[Error] No stations available to select.")
                return

            selected_station = self.stations[self.current_selection_index]
            station_title = selected_station['title'].strip()
            print(f"Attempting to play station: {station_title}")

            # Attempt to play the selected station
            try:
                uri = selected_station['uri']
                self.volumio_listener.play_webradio_station(station_title, uri)
                print(f"[Success] Playing station '{station_title}' with URI: {uri}")
            except Exception as e:
                print(f"[Error] Failed to play station '{station_title}': {e}")

    def display_no_stations_message(self):
        print("[RadioManager] Displaying 'No Stations Found' message on OLED.")
        image = Image.new(self.oled.mode, (self.oled.width, self.oled.height), "black")
        draw = ImageDraw.Draw(image)
        message = "No Stations Found"
        w, h = draw.textsize(message, font=self.font)
        x = (self.oled.width - w) / 2
        y = (self.oled.height - h) / 2
        draw.text((x, y), message, font=self.font, fill="white")
        self.oled.display(image)

    def clear_display(self):
        """Clear the OLED display."""
        image = Image.new(self.oled.mode, (self.oled.width, self.oled.height), "black")
        self.oled.display(image)
        print("[RadioManager] OLED display cleared.")
