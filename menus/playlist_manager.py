from PIL import Image, ImageDraw, ImageFont

class PlaylistManager:
    def __init__(self, oled, volumio_listener, mode_manager):
        self.oled = oled
        self.font_path = "/home/volumio/Quadify/fonts/OpenSans-Regular.ttf"
        try:
            self.font = ImageFont.truetype(self.font_path, 12)
        except IOError:
            print(f"Font file not found at {self.font_path}. Using default font.")
            self.font = ImageFont.load_default()

        self.playlists = []
        self.current_selection_index = 0
        self.is_active = False
        self.is_loading = False
        self.volumio_listener = volumio_listener
        self.mode_manager = mode_manager
        self.mode_manager.add_on_mode_change_callback(self.handle_mode_change)
        
        # Register playlists callback and fetch playlists immediately
        self.volumio_listener.register_playlists_callback(self.update_playlists)
        self.fetch_playlists()

    def fetch_playlists(self):
        """Fetch playlists from Volumio and display them immediately upon initialization."""
        print("[PlaylistManager] Fetching playlists on initialization...")
        self.is_loading = True
        self.volumio_listener.fetch_playlists()


    def handle_mode_change(self, current_mode):
        if current_mode == "playlist" and not self.is_active:
            print("Entering playlist mode...")
            self.start_playlist_mode()
        elif current_mode != "playlist" and self.is_active:
            print("Exiting playlist mode...")
            self.stop_playlist_mode()

    def start_playlist_mode(self):
        self.is_active = True
        self.current_selection_index = 0
        
        if not self.playlists:
            # If playlists haven't been fetched yet, display loading
            self.display_loading_screen()
            self.fetch_playlists()
        else:
            # If playlists are ready, display them immediately
            self.display_playlists()


    def display_loading_screen(self):
        self.clear_display()  # Clear display first
        image = Image.new(self.oled.mode, (self.oled.width, self.oled.height), "black")
        draw = ImageDraw.Draw(image)
        loading_text = "Loading Playlists..."
        w, h = draw.textsize(loading_text, font=self.font)
        x = (self.oled.width - w) / 2
        y = (self.oled.height - h) / 2
        draw.text((x, y), loading_text, font=self.font, fill="white")
        self.oled.display(image)

    def stop_playlist_mode(self):
        self.is_active = False
        self.clear_display()
        print(f"[PlaylistManager] Exiting playlist mode - is_active set to: {self.is_active}")

    def update_playlists(self, playlists):
        print(f"[PlaylistManager] update_playlists called - is_active: {self.is_active}, received playlists count: {len(playlists)}")

        # Assign playlists and log details
        self.playlists = playlists or []
        print(f"[PlaylistManager] After assignment - playlists count: {len(self.playlists)}")
        
        # Only display playlists if PlaylistManager is active
        if self.is_active:
            if self.playlists:
                print(f"[PlaylistManager] Displaying playlists: {[p['title'] for p in self.playlists]}")
                self.display_playlists()
            else:
                print("[PlaylistManager] No playlists to display; showing 'No Playlists Found' message.")
                self.display_no_playlists_message()
        else:
            print("[PlaylistManager] Playlists updated but not displayed as PlaylistManager is inactive.")



    def display_playlists(self):
        print(f"[PlaylistManager] Displaying playlists - is_active: {self.is_active}, playlists count: {len(self.playlists)}")
        
        if not self.playlists:
            print("[PlaylistManager] No playlists available in display_playlists. Showing 'No Playlists Found' message.")
            self.display_no_playlists_message()
            return

        # Proceed to display playlists if they exist
        image = Image.new(self.oled.mode, (self.oled.width, self.oled.height), "black")
        draw = ImageDraw.Draw(image)
        y_offset = 1
        x_offset = 10

        for i, playlist in enumerate(self.playlists):
            title = playlist['title']
            if i == self.current_selection_index:
                draw.text((x_offset, y_offset), "->", font=self.font, fill="white")
                draw.text((x_offset + 20, y_offset), title, font=self.font, fill="white")
            else:
                draw.text((x_offset + 20, y_offset), title, font=self.font, fill="gray")
            y_offset += 15

        self.oled.display(image)
        print("[PlaylistManager] Playlists displayed on OLED.")

    
    def scroll_selection(self, direction):
        print(f"[PlaylistManager] Received scroll direction: {direction}, playlists count: {len(self.playlists)}")

        if not self.playlists:
            print("[PlaylistManager] No playlists available to scroll.")
            return

        previous_index = self.current_selection_index

        if direction > 0:  # Scroll down
            self.current_selection_index = (self.current_selection_index + 1) % len(self.playlists)
        elif direction < 0:  # Scroll up
            self.current_selection_index = (self.current_selection_index - 1) % len(self.playlists)

        if previous_index != self.current_selection_index:
            print(f"[PlaylistManager] Scrolled to playlist index: {self.current_selection_index}")
            self.display_playlists()
        else:
            print("[PlaylistManager] Index unchanged; scroll input ignored.")



    def select_playlist(self):
        print(f"[PlaylistManager] Attempting to select playlist. is_active: {self.is_active}, playlists count: {len(self.playlists)}")

        # Confirm that the PlaylistManager is active before proceeding
        if not self.is_active:
            print("[PlaylistManager] PlaylistManager is not active. Cannot select playlist.")
            return

        # Check if there are any playlists to select from
        if self.playlists:
            # Ensure the current selection index is within bounds
            if 0 <= self.current_selection_index < len(self.playlists):
                selected_playlist = self.playlists[self.current_selection_index]
                playlist_title = selected_playlist['title']
                print(f"[PlaylistManager] Selected playlist: {playlist_title}")

                # Call to Volumio to play the selected playlist
                self.volumio_listener.play_playlist(playlist_title)
            else:
                print(f"[PlaylistManager] Selection index {self.current_selection_index} out of range for available playlists.")
        else:
            print("[PlaylistManager] No playlists available to select.")


    

    def display_no_playlists_message(self):
        self.clear_display()  # Clear screen before displaying message
        image = Image.new(self.oled.mode, (self.oled.width, self.oled.height), "black")
        draw = ImageDraw.Draw(image)
        message = "No Playlists Found"
        w, h = draw.textsize(message, font=self.font)
        x = (self.oled.width - w) / 2
        y = (self.oled.height - h) / 2
        draw.text((x, y), message, font=self.font, fill="white")
        self.oled.display(image)

    def clear_display(self):
        """Clears the OLED display by setting it to black."""
        if self.oled:
            image = Image.new(self.oled.mode, (self.oled.width, self.oled.height), "black")
            self.oled.display(image)
