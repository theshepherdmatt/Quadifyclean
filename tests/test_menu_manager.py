import pytest
from unittest.mock import MagicMock
from src.managers.menu_manager import MenuManager

@pytest.fixture
def menu_manager():
    # Mock dependencies for MenuManager
    display_manager = MagicMock()
    volumio_listener = MagicMock()
    mode_manager = MagicMock()

    # Initialize MenuManager with mocks
    return MenuManager(
        display_manager=display_manager,
        volumio_listener=volumio_listener,
        mode_manager=mode_manager
    )

def test_start_mode(menu_manager):
    """Test that start_mode activates menu and displays it."""
    menu_manager.start_mode()
    assert menu_manager.is_active is True
    assert menu_manager.current_selection_index == 0
    menu_manager.display_manager.draw_custom.assert_called_once()

def test_stop_mode(menu_manager):
    """Test that stop_mode deactivates menu and clears display."""
    menu_manager.start_mode()  # Start first to activate
    menu_manager.stop_mode()
    assert menu_manager.is_active is False
    print(f"clear_display call count: {menu_manager.display_manager.clear_display.call_count}")
    menu_manager.display_manager.clear_display.assert_called_once()  # Ensure clear_display is called once

def test_display_menu(menu_manager):
    """Test that display_menu draws the current menu with correct selection."""
    menu_manager.start_mode()  # Ensures menu is active
    menu_manager.display_menu()
    menu_manager.display_manager.draw_custom.assert_called()  # Verifies draw_custom is called

def test_scroll_selection(menu_manager):
    """Test that scroll_selection updates the selection index and redraws menu."""
    menu_manager.start_mode()  # Ensures menu is active
    initial_index = menu_manager.current_selection_index
    menu_manager.scroll_selection(1)  # Scroll down
    assert menu_manager.current_selection_index == (initial_index + 1) % len(menu_manager.current_menu_items)
    menu_manager.display_manager.draw_custom.assert_called()

def test_select_item(menu_manager):
    """Test that selecting an item triggers the correct mode transition."""
    menu_manager.start_mode()  # Ensures menu is active

    # Set index to "Webradio" and select item
    menu_manager.current_selection_index = menu_manager.current_menu_items.index("Webradio")
    menu_manager.select_item()
    menu_manager.mode_manager.to_webradio.assert_called_once()

    # Set index to "Playlists" and select item
    menu_manager.mode_manager.reset_mock()  # Reset the mock to verify only one call
    menu_manager.current_selection_index = menu_manager.current_menu_items.index("Playlists")
    menu_manager.select_item()
    menu_manager.mode_manager.to_playlist.assert_called_once()

    # Set index to "Favourites" and select item
    menu_manager.mode_manager.reset_mock()
    menu_manager.current_selection_index = menu_manager.current_menu_items.index("Favourites")
    menu_manager.select_item()
    menu_manager.mode_manager.to_favourites.assert_called_once()



