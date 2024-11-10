import unittest
import threading
from mode_Manager import ModeManager
from PIL import Image

# Updated Mock classes to satisfy the requirements for oled and clock arguments
class MockOLED:
    def __init__(self):
        self.mode = "RGB"  # Set this to whatever mode your actual OLED uses (e.g., "1" for monochrome)
        self.width = 128    # Set a reasonable placeholder width for the display
        self.height = 64    # Set a reasonable placeholder height for the display

    def draw(self, *args, **kwargs):
        pass

    def clear(self):
        pass

    def display(self, image):
        # This method is called when the screen needs to be updated
        pass

class MockClock:
    def __init__(self):
        self.running = False  # Default value for running status

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

class TestModeManager(unittest.TestCase):

    def setUp(self):
        """Set up a new instance of ModeManager for each test."""
        self.mock_oled = MockOLED()
        self.mock_clock = MockClock()
        self.mode_manager = ModeManager(self.mock_oled, self.mock_clock)

    def test_playback_mode(self):
        """Test that playback mode is correctly set when state is play and service is playback."""
        state = {
            "status": "play",
            "service": "music"
        }
        self.mode_manager.process_state_change(state)
        self.assertEqual(self.mode_manager.current_mode, "playback")

    def test_webradio_mode(self):
        """Test that webradio mode is correctly set when state is play and service is webradio."""
        state = {
            "status": "play",
            "service": "webradio"
        }
        self.mode_manager.process_state_change(state)
        self.assertEqual(self.mode_manager.current_mode, "webradio")

    def test_clock_mode_transition_after_stop(self):
        """Test that clock mode is correctly set after stop delay timer completes."""
        state = {
            "status": "stop",
            "service": ""
        }
        # Set up initial playback mode to simulate real usage
        self.mode_manager.current_mode = "playback"
        
        # Process stop state and wait for the delay to transition to clock mode
        self.mode_manager.process_state_change(state)
        
        # Wait for stop_delay_timer to trigger
        if self.mode_manager.stop_delay_timer:
            self.mode_manager.stop_delay_timer.join()
        
        self.assertEqual(self.mode_manager.current_mode, "clock")

    def test_no_redundant_mode_changes(self):
        """Test that no redundant mode changes occur (no flickering or duplicate mode)."""
        state = {
            "status": "play",
            "service": "webradio"
        }
        
        # Set mode to webradio initially
        self.mode_manager.set_mode("webradio", playback_state=state)
        initial_mode = self.mode_manager.current_mode
        
        # Process the same state again
        self.mode_manager.process_state_change(state)
        
        # Mode should still be webradio with no change
        self.assertEqual(initial_mode, self.mode_manager.current_mode)

    def test_transition_from_webradio_to_clock(self):
        """Test transitioning from webradio to clock mode smoothly after stopping."""
        # Set initial state to webradio
        state_play = {
            "status": "play",
            "service": "webradio"
        }
        self.mode_manager.process_state_change(state_play)
        self.assertEqual(self.mode_manager.current_mode, "webradio")
        
        # Now simulate stop state
        state_stop = {
            "status": "stop",
            "service": ""
        }
        self.mode_manager.process_state_change(state_stop)

        # Wait for stop_delay_timer to complete
        if self.mode_manager.stop_delay_timer:
            self.mode_manager.stop_delay_timer.join()

        # Verify that it switches to clock
        self.assertEqual(self.mode_manager.current_mode, "clock")

if __name__ == '__main__':
    unittest.main()
