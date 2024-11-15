import time
import pytest
from unittest.mock import MagicMock, patch
from src.display.clock import Clock

class MockDisplayManager:
    def __init__(self):
        self.oled = MagicMock(width=256, height=64)
        self.display_text = MagicMock()
        self.clear_screen = MagicMock()

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
