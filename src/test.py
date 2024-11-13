# tests/test_containers.py

import unittest
from unittest.mock import MagicMock, patch
from dependency_injector import providers
from containers import Container

class TestContainer(unittest.TestCase):
    def setUp(self):
        """
        Set up the test environment before each test.
        - Instantiate the Container.
        - Configure the Container with necessary configurations.
        - Mock external dependencies if necessary.
        """
        # Instantiate the container
        self.container = Container()

        # Configure the container with mock configuration
        self.container.config.volumio.host.from_value('localhost')
        self.container.config.volumio.port.from_value(3000)

        self.container.config.buttons.debounce_delay.from_value(0.2)

        self.container.config.pins.clk_pin.from_value(17)
        self.container.config.pins.dt_pin.from_value(18)
        self.container.config.pins.sw_pin.from_value(27)

    def test_volumio_listener_singleton(self):
        """
        Test that VolumioListener is a singleton and returns the same instance.
        """
        listener1 = self.container.volumio_listener()
        listener2 = self.container.volumio_listener()

        self.assertIs(listener1, listener2, "VolumioListener should be a singleton")

    def test_buttons_led_controller_factory(self):
        """
        Test that ButtonsLEDController is a factory and returns new instances.
        """
        controller1 = self.container.buttons_led_controller()
        controller2 = self.container.buttons_led_controller()

        self.assertIsNot(controller1, controller2, "ButtonsLEDController should be a factory and return new instances")

    def test_display_manager_singleton(self):
        """
        Test that DisplayManager is a singleton and returns the same instance.
        """
        display1 = self.container.display_manager()
        display2 = self.container.display_manager()

        self.assertIs(display1, display2, "DisplayManager should be a singleton")

    def test_clock_singleton(self):
        """
        Test that Clock is a singleton and returns the same instance.
        """
        clock1 = self.container.clock()
        clock2 = self.container.clock()

        self.assertIs(clock1, clock2, "Clock should be a singleton")

    def test_playback_manager_singleton(self):
        """
        Test that PlaybackManager is a singleton and returns the same instance.
        """
        playback1 = self.container.playback_manager()
        playback2 = self.container.playback_manager()

        self.assertIs(playback1, playback2, "PlaybackManager should be a singleton")

    def test_menu_manager_singleton(self):
        """
        Test that MenuManager is a singleton and returns the same instance.
        """
        menu1 = self.container.menu_manager()
        menu2 = self.container.menu_manager()

        self.assertIs(menu1, menu2, "MenuManager should be a singleton")

    def test_playlist_manager_singleton(self):
        """
        Test that PlaylistManager is a singleton and returns the same instance.
        """
        playlist1 = self.container.playlist_manager()
        playlist2 = self.container.playlist_manager()

        self.assertIs(playlist1, playlist2, "PlaylistManager should be a singleton")

    def test_radio_manager_singleton(self):
        """
        Test that RadioManager is a singleton and returns the same instance.
        """
        radio1 = self.container.radio_manager()
        radio2 = self.container.radio_manager()

        self.assertIs(radio1, radio2, "RadioManager should be a singleton")

    def test_tidal_manager_singleton(self):
        """
        Test that TidalManager is a singleton and returns the same instance.
        """
        tidal1 = self.container.tidal_manager()
        tidal2 = self.container.tidal_manager()

        self.assertIs(tidal1, tidal2, "TidalManager should be a singleton")

    def test_qobuz_manager_singleton(self):
        """
        Test that QobuzManager is a singleton and returns the same instance.
        """
        qobuz1 = self.container.qobuz_manager()
        qobuz2 = self.container.qobuz_manager()

        self.assertIs(qobuz1, qobuz2, "QobuzManager should be a singleton")

    def test_mode_manager_singleton(self):
        """
        Test that ModeManager is a singleton and correctly receives dependencies.
        """
        mode1 = self.container.mode_manager()
        mode2 = self.container.mode_manager()

        self.assertIs(mode1, mode2, "ModeManager should be a singleton")

        # Verify that mode_manager is correctly injected into managers
        self.assertIs(self.container.menu_manager().mode_manager, mode1, "ModeManager should be injected into MenuManager")
        self.assertIs(self.container.playlist_manager().mode_manager, mode1, "ModeManager should be injected into PlaylistManager")
        self.assertIs(self.container.radio_manager().mode_manager, mode1, "ModeManager should be injected into RadioManager")
        self.assertIs(self.container.tidal_manager().mode_manager, mode1, "ModeManager should be injected into TidalManager")
        self.assertIs(self.container.qobuz_manager().mode_manager, mode1, "ModeManager should be injected into QobuzManager")

    def test_rotary_control_factory(self):
        """
        Test that RotaryControl is a factory and returns new instances with correct pin configurations.
        """
        rotary1 = self.container.rotary_control()
        rotary2 = self.container.rotary_control()

        self.assertIsNot(rotary1, rotary2, "RotaryControl should be a factory and return new instances")

        # Verify that the pins are correctly passed
        self.assertEqual(rotary1.clk_pin, 17, "RotaryControl clk_pin should be 17")
        self.assertEqual(rotary1.dt_pin, 18, "RotaryControl dt_pin should be 18")
        self.assertEqual(rotary1.sw_pin, 27, "RotaryControl sw_pin should be 27")

    def test_state_handler_singleton(self):
        """
        Test that StateHandler is a singleton and correctly receives dependencies.
        """
        handler1 = self.container.state_handler()
        handler2 = self.container.state_handler()

        self.assertIs(handler1, handler2, "StateHandler should be a singleton")
        self.assertIs(handler1.volumio_listener, self.container.volumio_listener(), "StateHandler should receive the correct VolumioListener")
        self.assertIs(handler1.mode_manager, self.container.mode_manager(), "StateHandler should receive the correct ModeManager")

    def test_logger_initialization(self):
        """
        Test that the container initializes without errors and logs the initialization.
        """
        with self.assertLogs('containers', level='DEBUG') as log:
            container = Container()
            container.config.from_dict({
                'volumio': {'host': 'localhost', 'port': 3000},
                'buttons': {'debounce_delay': 0.2},
                'pins': {'clk_pin': 17, 'dt_pin': 18, 'sw_pin': 27}
            })
            container.volumio_listener()
        
        # Check that the initialization log is present
        self.assertIn('Container initialized with all components', log.output[-1])

    def test_missing_configuration(self):
        """
        Test that missing configuration values raise appropriate errors.
        """
        # Create a new container without setting required configurations
        container = Container()

        # Attempt to retrieve a component that requires configuration
        with self.assertRaises(providers.errors.ProvidersError):
            container.volumio_listener()

    def test_circular_dependency_handling(self):
        """
        Test that circular dependencies are handled gracefully.
        """
        # Assuming that ModeManager and other managers have no circular dependencies now,
        # this test ensures that ModeManager is injected correctly.

        mode = self.container.mode_manager()

        # Verify that ModeManager's dependencies are correctly set
        self.assertIs(mode.menu_manager.mode_manager, mode, "MenuManager should have ModeManager injected")
        self.assertIs(mode.playlist_manager.mode_manager, mode, "PlaylistManager should have ModeManager injected")
        self.assertIs(mode.radio_manager.mode_manager, mode, "RadioManager should have ModeManager injected")
        self.assertIs(mode.tidal_manager.mode_manager, mode, "TidalManager should have ModeManager injected")
        self.assertIs(mode.qobuz_manager.mode_manager, mode, "QobuzManager should have ModeManager injected")

    def test_full_dependency_graph(self):
        """
        Test the full dependency graph by retrieving all components and ensuring they're correctly instantiated.
        """
        # Retrieve all components
        volumio_listener = self.container.volumio_listener()
        buttons_led_controller = self.container.buttons_led_controller()
        display_manager = self.container.display_manager()
        clock = self.container.clock()
        playback_manager = self.container.playback_manager()
        menu_manager = self.container.menu_manager()
        playlist_manager = self.container.playlist_manager()
        radio_manager = self.container.radio_manager()
        tidal_manager = self.container.tidal_manager()
        qobuz_manager = self.container.qobuz_manager()
        mode_manager = self.container.mode_manager()
        rotary_control = self.container.rotary_control()
        state_handler = self.container.state_handler()

        # Assertions to ensure all components are instantiated
        self.assertIsNotNone(volumio_listener)
        self.assertIsNotNone(buttons_led_controller)
        self.assertIsNotNone(display_manager)
        self.assertIsNotNone(clock)
        self.assertIsNotNone(playback_manager)
        self.assertIsNotNone(menu_manager)
        self.assertIsNotNone(playlist_manager)
        self.assertIsNotNone(radio_manager)
        self.assertIsNotNone(tidal_manager)
        self.assertIsNotNone(qobuz_manager)
        self.assertIsNotNone(mode_manager)
        self.assertIsNotNone(rotary_control)
        self.assertIsNotNone(state_handler)

        # Verify singleton properties
        self.assertIs(volumio_listener, self.container.volumio_listener())
        self.assertIs(display_manager, self.container.display_manager())
        self.assertIs(clock, self.container.clock())
        self.assertIs(playback_manager, self.container.playback_manager())
        self.assertIs(menu_manager, self.container.menu_manager())
        self.assertIs(playlist_manager, self.container.playlist_manager())
        self.assertIs(radio_manager, self.container.radio_manager())
        self.assertIs(tidal_manager, self.container.tidal_manager())
        self.assertIs(qobuz_manager, self.container.qobuz_manager())
        self.assertIs(mode_manager, self.container.mode_manager())
        self.assertIs(state_handler, self.container.state_handler())

        # Verify factory property for RotaryControl
        rotary1 = self.container.rotary_control()
        rotary2 = self.container.rotary_control()
        self.assertIsNot(rotary1, rotary2, "RotaryControl should be a factory and return new instances")

    if __name__ == '__main__':
        unittest.main()