# menus/tidal_manager.py
from PIL import Image, ImageDraw, ImageFont

class TidalManager:
    def __init__(self, oled, volumio_listener, mode_manager):
        # Initialize essential components
        self.oled = oled
        self.volumio_listener = volumio_listener
        self.mode_manager = mode_manager
        
        # Set up initial menu and display state
        self.current_menu = "categories"  # Start in the categories menu by default
        self.current_selection_index = 0
        self.categories = ["Tidal Playlists", "Tidal Albums", "Tidal Tracks"]
        self.tidal_content = []

        # Set up the font
        self.font_path = "/home/volumio/Quadify/fonts/OpenSans-Regular.ttf"
        try:
            self.font = ImageFont.truetype(self.font_path, 12)
        except IOError:
            print(f"Font file not found at {self.font_path}. Using default font.")
            self.font = ImageFont.load_default()

        # Register callback to update Tidal content when fetched from Volumio
        self.volumio_listener.register_tidal_callback(self.update_tidal_content)

        # Display the categories initially
        self.display_categories()
        print("[TidalManager] Initialized and displayed categories.")

    def start_tidal_mode(self):
        print("Entering Tidal mode and fetching content.")
        self.volumio_listener.fetch_tidal_content('tidal/playlists')  # Fetch Tidal content
        self.display_categories()  # Display categories on the OLED

    def stop_mode(self):
        print("Exiting Tidal mode...")
        self.clear_display()

    def handle_mode_change(self, new_mode):
        print(f"[Debug] Handling mode change. New mode: {new_mode}, Current menu: {self.current_menu}")
        if new_mode == "tidal":
            print("[TidalManager] Mode changed to 'tidal'. Starting Tidal mode.")
            self.start_tidal_mode()
        elif new_mode != "tidal" and self.current_menu != "categories":
            print("[TidalManager] Mode changed away from 'tidal'. Stopping Tidal mode.")
            self.stop_mode()

    def display_categories(self):
        image = Image.new(self.oled.mode, (self.oled.width, self.oled.height), "black")
        draw = ImageDraw.Draw(image)
        y_offset = 0
        x_offset = 10

        for i, category in enumerate(self.categories):
            if i == self.current_selection_index:
                draw.text((x_offset, y_offset), "->", font=self.font, fill="white")
                draw.text((x_offset + 20, y_offset), category, font=self.font, fill="white")
            else:
                draw.text((x_offset + 20, y_offset), category, font=self.font, fill="gray")
            y_offset += 15

        self.oled.display(image)

    def display_tidal_content(self):
        if not self.tidal_content:
            print("No Tidal content to display.")
            self.display_no_content_message()
            return

        image = Image.new(self.oled.mode, (self.oled.width, self.oled.height), "black")
        draw = ImageDraw.Draw(image)
        y_offset = 0
        x_offset = 10

        for i, item in enumerate(self.tidal_content):
            title = item['title']
            if i == self.current_selection_index:
                draw.text((x_offset, y_offset), "->", font=self.font, fill="white")
                draw.text((x_offset + 20, y_offset), title, font=self.font, fill="white")
            else:
                draw.text((x_offset + 20, y_offset), title, font=self.font, fill="gray")
            y_offset += 15

        self.oled.display(image)

    def scroll_selection(self, direction):
        if self.current_menu == "categories":
            options = self.categories
        else:
            options = self.tidal_content

        if not options:
            return

        previous_index = self.current_selection_index
        if direction > 0:  # Scroll down
            self.current_selection_index = (self.current_selection_index + 1) % len(options)
        elif direction < 0:  # Scroll up
            self.current_selection_index = (self.current_selection_index - 1) % len(options)

        if previous_index != self.current_selection_index:
            print(f"Scrolled to index: {self.current_selection_index}")
            if self.current_menu == "categories":
                self.display_categories()
            else:
                self.display_tidal_content()

    def select_item(self):
        if self.current_menu == "categories":
            selected_category = self.categories[self.current_selection_index]
            print(f"Selected Tidal category: {selected_category}")

            # Fetch content based on the selected category
            if selected_category == "Tidal Playlists":
                print("Fetching Tidal Playlists...")
                self.volumio_listener.fetch_tidal_content('tidal/playlists')
            elif selected_category == "Tidal Albums":
                print("Fetching Tidal Albums...")
                self.volumio_listener.fetch_tidal_content('tidal/albums')
            elif selected_category == "Tidal Tracks":
                print("Fetching Tidal Tracks...")
                self.volumio_listener.fetch_tidal_content('tidal/tracks')
            else:
                print(f"Unknown Tidal category: {selected_category}")

            self.current_menu = "tidal_content"
            self.current_selection_index = 0
            print(f"Switched to Tidal content menu for category: {selected_category}")

        elif self.current_menu == "tidal_content":
            if not self.tidal_content:
                print("No Tidal content available to select.")
                return

            selected_item = self.tidal_content[self.current_selection_index]
            print(f"Selected Tidal item: {selected_item['title']}")
            self.volumio_listener.play_track(selected_item['uri'])

    def update_tidal_content(self, content):
        """Update the list of available Tidal content."""
        self.tidal_content = [
            {'title': item.get('title', '').strip(), 'uri': item.get('uri', '').strip()}
            for item in content
        ]

        if not content:
            print("[Error] No Tidal content available to display.")
            self.display_no_content_message()
        else:
            print(f"[Debug] Tidal content has been updated: {[item['title'] for item in content]}")
            self.display_tidal_content()

    def display_no_content_message(self):
        """Display a message if no Tidal content is available."""
        image = Image.new(self.oled.mode, (self.oled.width, self.oled.height), "black")
        draw = ImageDraw.Draw(image)
        message = "No Content Found"
        w, h = draw.textsize(message, font=self.font)
        x = (self.oled.width - w) / 2
        y = (self.oled.height - h) / 2
        draw.text((x, y), message, font=self.font, fill="white")
        self.oled.display(image)

    def clear_display(self):
        """Clear the OLED display."""
        image = Image.new(self.oled.mode, (self.oled.width, self.oled.height), "black")
        self.oled.display(image)
        print("OLED display cleared by TidalManager.")

