import pytest
from unittest.mock import MagicMock
from src.managers.mode_manager import ModeManager

@pytest.fixture
def mode_manager():
    # Mock dependencies for ModeManager
    display_manager = MagicMock()
    clock = MagicMock()
    playback = MagicMock()
    menu_manager = MagicMock()
    playlist_manager = MagicMock()
    radio_manager = MagicMock()
    tidal_manager = MagicMock()

    # Initialize ModeManager with mocks
    return ModeManager(
        display_manager=display_manager,
        clock=clock,
        playback=playback,
        menu_manager=menu_manager,
        playlist_manager=playlist_manager,
        radio_manager=radio_manager,
        tidal_manager=tidal_manager
    )

def test_initial_state(mode_manager):
    """Test that ModeManager initializes in 'clock' mode and calls enter_clock."""
    assert mode_manager.get_mode() == 'clock'
    mode_manager.clock.start.assert_called_once()  # Verify clock mode is initiated

def test_transition_to_playback(mode_manager):
    """Test transition from 'clock' to 'playback' mode."""
    mode_manager.to_playback()
    assert mode_manager.get_mode() == 'playback'
    mode_manager.playback.start.assert_called_once()
    mode_manager.clock.stop.assert_called_once()

def test_transition_to_menu(mode_manager):
    """Test transition from 'clock' to 'menu' mode."""
    mode_manager.to_menu()
    assert mode_manager.get_mode() == 'menu'
    mode_manager.menu_manager.start_mode.assert_called_once()
    mode_manager.clock.stop.assert_called_once()

def test_transition_to_webradio(mode_manager):
    """Test transition from 'clock' to 'webradio' mode."""
    mode_manager.to_webradio()
    assert mode_manager.get_mode() == 'webradio'
    mode_manager.radio_manager.start_mode.assert_called_once()
    mode_manager.clock.stop.assert_called_once()

def test_transition_to_tidal(mode_manager):
    """Test transition from 'clock' to 'tidal' mode."""
    mode_manager.to_tidal()
    assert mode_manager.get_mode() == 'tidal'
    mode_manager.tidal_manager.start_mode.assert_called_once()
    mode_manager.clock.stop.assert_called_once()

def test_callback_on_mode_change(mode_manager):
    """Test that mode change callbacks are invoked."""
    callback = MagicMock()
    mode_manager.add_on_mode_change_callback(callback)

    # Trigger a mode change
    mode_manager.to_playback()
    callback.assert_called_once_with('playback')  # Verify callback is invoked with 'playback' mode

def test_process_state_change_play(mode_manager):
    """Test that process_state_change triggers playback when status is 'play'."""
    mode_manager.process_state_change({"status": "play"})
    assert mode_manager.get_mode() == 'playback'
    mode_manager.playback.start.assert_called_once()

def test_process_state_change_stop(mode_manager):
    """Test that process_state_change triggers clock mode when status is 'stop'."""
    mode_manager.to_playback()  # Set to playback first
    mode_manager.process_state_change({"status": "stop"})
    assert mode_manager.get_mode() == 'clock'
    mode_manager.clock.start.assert_called()

