# src/managers/mode_manager.py

from transitions import Machine
import threading
import logging

class ModeManager:
    states = [
        {'name': 'clock', 'on_enter': 'enter_clock'},
        {'name': 'playback', 'on_enter': 'enter_playback'},
        {'name': 'menu', 'on_enter': 'enter_menu'},
        {'name': 'webradio', 'on_enter': 'enter_webradio'},
        {'name': 'playlist', 'on_enter': 'enter_playlist'},
        {'name': 'favourites', 'on_enter': 'enter_favourites'},
        {'name': 'tidal', 'on_enter': 'enter_tidal'},
    ]

    def __init__(self, display_manager, clock, playback, menu_manager, playlist_manager, radio_manager, tidal_manager):
        self.display_manager = display_manager
        self.clock = clock
        self.playback = playback
        self.menu_manager = menu_manager
        self.playlist_manager = playlist_manager
        self.radio_manager = radio_manager
        self.tidal_manager = tidal_manager

        # Set up logging
        self.logger = logging.getLogger(self.__class__.__name__)
        logging.basicConfig(level=logging.DEBUG)

        self.machine = Machine(
            model=self,
            states=ModeManager.states,
            initial='clock',
            auto_transitions=False
        )

        # Define transitions without 'before' since 'on_enter' handles method calls
        self.machine.add_transition(trigger='to_playback', source='*', dest='playback')
        self.machine.add_transition(trigger='to_menu', source='*', dest='menu')
        self.machine.add_transition(trigger='to_webradio', source='*', dest='webradio')
        self.machine.add_transition(trigger='to_playlist', source='*', dest='playlist')
        self.machine.add_transition(trigger='to_favourites', source='*', dest='favourites')
        self.machine.add_transition(trigger='to_tidal', source='*', dest='tidal')
        self.machine.add_transition(trigger='to_clock', source='*', dest='clock')

        self.on_mode_change_callbacks = []
        self.lock = threading.Lock()

        # Explicitly call 'enter_clock' to ensure initial state is set
        self.enter_clock()

    # Define enter methods with 'event' parameter
    def enter_playback(self, event=None):
        self.logger.debug("Entering playback mode.")
        self.clock.stop()
        self.menu_manager.stop_mode()
        self.playback.start()
        self.notify_mode_change('playback')

    def enter_menu(self, event=None):
        self.logger.debug("Entering menu mode.")
        self.clock.stop()
        self.playback.stop()
        self.menu_manager.start_mode()
        self.notify_mode_change('menu')

    def enter_webradio(self, event=None):
        self.logger.debug("Entering webradio mode.")
        self.clock.stop()
        self.playback.stop()
        self.radio_manager.start_mode()
        self.notify_mode_change('webradio')

    def enter_playlist(self, event=None):
        self.logger.debug("Entering playlist mode.")
        self.clock.stop()
        self.playback.stop()
        self.playlist_manager.start_mode()
        self.notify_mode_change('playlist')

    def enter_favourites(self, event=None):
        self.logger.debug("Entering favourites mode.")
        self.clock.stop()
        self.playback.stop()
        # Implement favourites mode logic here
        self.notify_mode_change('favourites')

    def enter_tidal(self, event=None):
        self.logger.debug("Entering tidal mode.")
        self.clock.stop()
        self.playback.stop()
        self.tidal_manager.start_mode()
        self.notify_mode_change('tidal')

    def enter_clock(self, event=None):
        self.logger.debug("Entering clock mode.")
        self.playback.stop()
        self.menu_manager.stop_mode()
        self.radio_manager.stop_mode()
        self.playlist_manager.stop_mode()
        self.tidal_manager.stop_mode()
        self.clock.start()
        self.notify_mode_change('clock')

    def process_state_change(self, state):
        status = state.get("status", "")
        self.logger.debug(f"Processing state change with status: {status}")
        if status == "play":
            self.to_playback()
        elif status in ["pause", "stop"]:
            self.to_clock()

    def add_on_mode_change_callback(self, callback):
        with self.lock:
            if callable(callback):
                self.on_mode_change_callbacks.append(callback)
                self.logger.debug(f"Added mode change callback: {callback}")

    def notify_mode_change(self, current_mode):
        with self.lock:
            self.logger.debug(f"Notifying mode change to: {current_mode}")
            for callback in self.on_mode_change_callbacks:
                try:
                    self.logger.debug(f"Invoking callback: {callback}")
                    callback(current_mode)
                except Exception as e:
                    self.logger.error(f"ModeManager: Error in callback {callback}: {e}")

    def get_mode(self):
        return self.state

    def stop(self):
        """Optional: Method to clean up if needed."""
        pass
