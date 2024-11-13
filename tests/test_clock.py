# tests/test_clock.py

from src.display.clock import Clock

def test_clock_initialization():
    """Test that the clock can be initialized properly."""
    class MockDevice:
        def __init__(self):
            self.mode = 'RGB'
            self.width = 256
            self.height = 64

    mock_device = MockDevice()
    mock_config = {}  # or create a MagicMock if config requires certain attributes

    clock = Clock(mock_device, mock_config)  # Pass the mock config
    assert clock is not None
