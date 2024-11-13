import unittest
from unittest.mock import MagicMock, patch
from src.hardware.buttonsleds import ButtonsLEDController
from src.network.volumio_listener import VolumioListener


class TestButtonsLEDController(unittest.TestCase):
    def setUp(self):
        # Create a mock VolumioListener with signal attributes
        self.mock_volumio_listener = MagicMock(spec=VolumioListener)
        self.mock_volumio_listener.state_changed = MagicMock()
        self.mock_volumio_listener.connected = MagicMock()
        self.mock_volumio_listener.disconnected = MagicMock()
        
        # Patch smbus2 to prevent actual I2C interaction
        with patch('smbus2.SMBus'):
            # Provide a custom config path, or use the default if already provided in `config.yaml`
            self.controller = ButtonsLEDController(self.mock_volumio_listener, config_path='path/to/test/config.yaml')

    def test_on_connect_updates_led(self):
        # Call the on_connect directly and verify side effects in controller
        self.controller.on_connect()
        
        # Check if the on_connect updated internal states or LEDs (example check)
        # Here you can check if any expected LED state was set
        # self.assertEqual(self.controller.status_led_state, expected_value)

    def test_on_disconnect_updates_led(self):
        # Call the on_disconnect directly and verify side effects in controller
        self.controller.on_disconnect()
        
        # Check if the on_disconnect updated internal states or LEDs (example check)
        # Here you can check if any expected LED state was cleared or set
        # self.assertEqual(self.controller.status_led_state, expected_value)

    def test_volumio_listener_state_change_updates_leds(self):
        # Create a sample state to simulate state change
        sample_state = {"status": "play"}
        
        # Simulate the state change event
        self.controller.on_state(None, sample_state)
        
        # Check that the LED state was updated based on "play" status
        expected_led_state = self.controller.status_led_state
        self.assertEqual(expected_led_state, 0b10000000)  # LED1 value based on play status


if __name__ == '__main__':
    unittest.main()

