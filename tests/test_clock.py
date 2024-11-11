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
    clock = Clock(mock_device)
    
    assert clock.device == mock_device
    assert clock.running is False

