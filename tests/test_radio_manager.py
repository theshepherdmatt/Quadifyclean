import pytest
from unittest.mock import MagicMock
from src.managers.radio_manager import RadioManager

@pytest.fixture
def radio_manager():
    # Mock dependencies for RadioManager
    display_manager = MagicMock()
    volumio_listener = MagicMock()
    mode_manager = MagicMock()

    # Initialize RadioManager with mocks
    return RadioManager(
        display_manager=display_manager,
        volumio_listener=volumio_listener,
        mode_manager=mode_manager
    )

def test_start_mode_with_no_stations(radio_manager):
    """Test that start_mode displays loading and fetches stations when list is empty."""
    radio_manager.radio_stations = []  # Ensure the station list is empty
    radio_manager.start_mode()
    assert radio_manager.is_active is True
    radio_manager.display_manager.display_text.assert_called_with(
        "Loading Radios...",
        position=(radio_manager.display_manager.oled.width // 2, radio_manager.display_manager.oled.height // 2),
        font_key='menu_font'
    )
    radio_manager.volumio_listener.fetch_webradio_stations.assert_called_once()

def test_start_mode_with_stations(radio_manager):
    """Test that start_mode displays stations when list is populated."""
    radio_manager.radio_stations = [{"title": "Station 1", "uri": "uri1"}]
    radio_manager.start_mode()
    assert radio_manager.is_active is True
    radio_manager.display_manager.draw_custom.assert_called_once()

def test_stop_mode(radio_manager):
    """Test that stop_mode deactivates radio manager and clears display."""
    radio_manager.start_mode()  # Start first to activate
    radio_manager.stop_mode()
    assert radio_manager.is_active is False
    radio_manager.display_manager.clear_display.assert_called_once()

def test_update_radio_stations(radio_manager):
    """Test updating radio stations and displaying them."""
    radio_manager.start_mode()  # Start the mode to ensure it is active
    mock_stations = [
        {"title": "Station 1", "uri": "uri1"},
        {"title": "Station 2", "uri": "uri2"}
    ]
    radio_manager.update_radio_stations(mock_stations)
    assert len(radio_manager.radio_stations) == 2
    assert radio_manager.radio_stations[0]["title"] == "Station 1"
    radio_manager.display_manager.draw_custom.assert_called_once()  # Verifies the display was updated


def test_scroll_selection(radio_manager):
    """Test that scroll_selection updates the selection index and redraws the stations."""
    radio_manager.radio_stations = [{"title": "Station 1", "uri": "uri1"}, {"title": "Station 2", "uri": "uri2"}]
    radio_manager.start_mode()  # Ensures mode is active
    initial_index = radio_manager.current_selection_index
    radio_manager.scroll_selection(1)  # Scroll down
    assert radio_manager.current_selection_index == (initial_index + 1) % len(radio_manager.radio_stations)
    radio_manager.display_manager.draw_custom.assert_called()

def test_select_item(radio_manager):
    """Test that selecting a radio station triggers playback."""
    radio_manager.radio_stations = [{"title": "Station 1", "uri": "uri1"}, {"title": "Station 2", "uri": "uri2"}]
    radio_manager.start_mode()  # Ensures mode is active
    radio_manager.current_selection_index = 1  # Select the second station
    radio_manager.select_item()
    radio_manager.volumio_listener.play_webradio_station.assert_called_once_with(
        title="Station 2",
        uri="uri2"
    )

def test_handle_mode_change(radio_manager):
    """Test that handle_mode_change starts or stops the radio manager based on mode."""
    # Reset mock to ensure isolation from previous calls
    radio_manager.display_manager.draw_custom.reset_mock()

    # Add some mock stations to avoid the loading state
    radio_manager.radio_stations = [
        {"title": "Station 1", "uri": "uri1"},
        {"title": "Station 2", "uri": "uri2"}
    ]
    
    # When mode is "webradio", start_mode should be called
    print("Handling mode change to 'webradio'")
    radio_manager.handle_mode_change("webradio")
    
    assert radio_manager.is_active is True, "RadioManager should be active after changing mode to 'webradio'"
    
    # Adding a debug log to confirm we reached this step
    print("Checking if draw_custom was called after handling 'webradio' mode change")
    try:
        radio_manager.display_manager.draw_custom.assert_called()
    except AssertionError:
        print("Failed: draw_custom was not called as expected.")
        raise

    # Reset mock for subsequent checks
    radio_manager.display_manager.draw_custom.reset_mock()

    # When mode changes away from "webradio", stop_mode should be called
    print("Handling mode change to 'playback'")
    radio_manager.handle_mode_change("playback")
    
    assert radio_manager.is_active is False, "RadioManager should not be active after changing mode to 'playback'"
    radio_manager.display_manager.clear_display.assert_called()
