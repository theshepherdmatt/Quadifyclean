import time
import pytest
from unittest.mock import MagicMock, patch
from src.display.clock import Clock
from src.managers.mode_manager import ModeManager

class MockDisplayManager:
    def __init__(self):
        self.oled = MagicMock(width=256, height=64)
        self.display_text = MagicMock()
        self.clear_screen = MagicMock()
        
class MockPlayback:
    def __init__(self):
        self.start = MagicMock()
        self.stop = MagicMock()

class MockMenuManager:
    def __init__(self):
        self.start_mode = MagicMock()
        self.stop_mode = MagicMock()

def test_clock_initialization():
    """Test that the clock can be initialized properly."""
    mock_display_manager = MockDisplayManager()
    mock_config = {}  # or create a MagicMock if config requires certain attributes

    clock = Clock(mock_display_manager, mock_config)  # Pass the mock config
    assert clock is not None

def test_draw_clock():
    """Test that the clock draws the correct time."""
    mock_display_manager = MockDisplayManager()
    clock = Clock(mock_display_manager, config={})

    with patch('time.strftime', return_value="12:34"):
        # Call the draw_clock method
        clock.draw_clock()

        # Verify that display_text is called with expected arguments
        mock_display_manager.display_text.assert_called_once_with(
            text="12:34",
            position=(mock_display_manager.oled.width // 2, mock_display_manager.oled.height // 2),
            font_key='clock_large'
        )

def test_clock_start_and_stop():
    """Test starting and stopping the clock."""
    mock_display_manager = MockDisplayManager()
    mock_config = {}
    clock = Clock(mock_display_manager, mock_config)

    with patch.object(clock, 'update_clock', wraps=clock.update_clock) as mock_update_clock:
        clock.start()
        time.sleep(0.1)  # Allow the thread to start and run
        clock.stop()

        # Verify that update_clock was called (the clock thread ran)
        assert mock_update_clock.call_count > 0

    # Verify that the display was cleared when stopping the clock
    mock_display_manager.clear_screen.assert_called_once()

def test_mode_manager_transitions():
    """Test that ModeManager transitions between different modes correctly."""
    # Set up mock dependencies
    mock_display_manager = MockDisplayManager()
    mock_clock = MagicMock()
    mock_playback = MockPlayback()
    mock_menu_manager = MockMenuManager()
    mock_playlist_manager = MagicMock()
    mock_radio_manager = MagicMock()
    mock_tidal_manager = MagicMock()

    # Initialize ModeManager with mocks
    mode_manager = ModeManager(
        display_manager=mock_display_manager,
        clock=mock_clock,
        playback=mock_playback,
        menu_manager=mock_menu_manager,
        playlist_manager=mock_playlist_manager,
        radio_manager=mock_radio_manager,
        tidal_manager=mock_tidal_manager
    )

    # Test initial state is 'clock'
    assert mode_manager.get_mode() == 'clock'
    mock_clock.start.assert_called_once()

    # Test transition to 'playback'
    mode_manager.to_playback()
    assert mode_manager.get_mode() == 'playback'
    mock_playback.start.assert_called_once()
    mock_clock.stop.assert_called_once()

    # Test transition to 'menu'
    mode_manager.to_menu()
    assert mode_manager.get_mode() == 'menu'
    mock_menu_manager.start_mode.assert_called_once()
    mock_playback.stop.assert_called()

    # Test transition to 'webradio'
    mode_manager.to_webradio()
    assert mode_manager.get_mode() == 'webradio'
    mock_radio_manager.start_mode.assert_called_once()
    mock_menu_manager.stop_mode.assert_called()

    # Test transition to 'playlist'
    mode_manager.to_playlist()
    assert mode_manager.get_mode() == 'playlist'
    mock_playlist_manager.start_mode.assert_called_once()
    mock_radio_manager.stop_mode.assert_called()

    # Test transition to 'tidal'
    mode_manager.to_tidal()
    assert mode_manager.get_mode() == 'tidal'
    mock_tidal_manager.start_mode.assert_called_once()
    mock_playlist_manager.stop_mode.assert_called()

    # Test transition back to 'clock'
    mode_manager.to_clock()
    assert mode_manager.get_mode() == 'clock'
    mock_clock.start.assert_called()
    mock_tidal_manager.stop_mode.assert_called()
