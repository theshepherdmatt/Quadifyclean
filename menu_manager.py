from PIL import Image, ImageDraw, ImageFont

class MenuManager:
    def __init__(self, oled, volumio_listener, mode_manager):
        self.oled = oled
        self.font_path = "/home/volumio/Quadify/fonts/OpenSans-Regular.ttf"
        try:
            self.font = ImageFont.truetype(self.font_path, 12)
        except IOError:
            print(f"Font file not found at {self.font_path}. Using default font.")
            self.font = ImageFont.load_default()

        self.menu_stack = []  # Stack to keep track of menu levels
        self.current_menu_items = []  # Items in the current menu
        self.current_selection_index = 0
        self.is_active = False  # Indicates if menu mode is currently active
        self.volumio_listener = volumio_listener

        # Register callbacks
        self.mode_manager = mode_manager
        self.mode_manager.add_on_mode_change_callback(self.handle_mode_change)

    def handle_mode_change(self, current_mode):
        print(f"MenuManager handling mode change to: {current_mode}")
        if current_mode == "menu":
            print("Entering menu mode...")
            self.start_menu_mode()
        else:
            if self.is_active:
                print("Exiting menu mode...")
                self.stop_menu_mode()

    def start_menu_mode(self):
        print("Starting menu mode...")
        self.is_active = True
        self.menu_stack = []  # Reset the menu stack
        self.current_selection_index = 0
        self.current_menu_items = ["Webradio", "Playlists", "Favourites"]
        self.display_menu()

    def stop_menu_mode(self):
        print("Stopping menu mode...")
        self.is_active = False
        self.clear_display()

    def display_menu(self):
        max_visible_items = 4  # Number of items visible on the screen
        total_items = len(self.current_menu_items)

        # Calculate the visible window of menu items
        start_index = max(0, min(self.current_selection_index - max_visible_items // 2, total_items - max_visible_items))
        end_index = min(start_index + max_visible_items, total_items)

        image = Image.new(self.oled.mode, (self.oled.width, self.oled.height), "black")
        draw = ImageDraw.Draw(image)
        y_offset = 1
        x_offset = 10

        # Draw the visible menu items within the calculated window
        for i in range(start_index, end_index):
            item = self.current_menu_items[i]
            if i == self.current_selection_index:
                draw.text((x_offset, y_offset), "->", font=self.font, fill="white")
                draw.text((x_offset + 20, y_offset), item, font=self.font, fill="white")
            else:
                draw.text((x_offset + 20, y_offset), item, font=self.font, fill="gray")
            y_offset += 15

        self.oled.display(image)
        print(f"[MenuManager] Displaying menu items from index {start_index} to {end_index}. Current selection index: {self.current_selection_index}")


    def scroll_selection(self, direction):
        if not self.is_active:
            return

        previous_index = self.current_selection_index
        if direction > 0:  # Scroll down
            self.current_selection_index = (self.current_selection_index + 1) % len(self.current_menu_items)
        elif direction < 0:  # Scroll up
            self.current_selection_index = (self.current_selection_index - 1) % len(self.current_menu_items)

        if previous_index != self.current_selection_index:
            print(f"Scrolled to menu index: {self.current_selection_index}")
            self.display_menu()

    def handle_rotation(self, direction):
        if direction == "Clockwise":
            self.scroll_selection(1)
        elif direction == "Counterclockwise":
            self.scroll_selection(-1)
        mode_manager.reset_timer()  # Reset inactivity timer


    def select_item(self):
        if not self.is_active:
            return

        if self.current_menu_items:
            selected_item = self.current_menu_items[self.current_selection_index]
            print(f"Selected menu item: {selected_item}")

            # Handle selection based on the current menu level
            if not self.menu_stack:
                # We're at the main menu
                if selected_item == "Webradio":
                    print("Switching to webradio mode.")
                    self.mode_manager.set_mode("webradio")
                elif selected_item == "Playlists":
                    print("Switching to playlist mode.")
                    self.mode_manager.set_mode("playlist")
                elif selected_item == "Favourites":
                    print("Switching to favourites mode.")
                    self.mode_manager.set_mode("favourites")
            else:
                # Handle submenus if any exist
                pass
        else:
            print("No items to select.")

    def go_back(self):
        if self.menu_stack:
            # Go back to the previous menu level
            self.current_menu_items = self.menu_stack.pop()
            self.current_selection_index = 0
            self.display_menu()
        else:
            # Already at the main menu; exit menu mode
            print("Exiting to clock mode.")
            self.mode_manager.set_mode("clock")

    def clear_display(self):
        # Clear the OLED display
        image = Image.new(self.oled.mode, (self.oled.width, self.oled.height), "black")
        self.oled.display(image)
        print("OLED display cleared by MenuManager.")
