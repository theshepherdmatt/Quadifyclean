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
        {'name': 'qobuz', 'on_enter': 'enter_qobuz'},  # Added Qobuz mode
    ]

    def __init__(self, display_manager, clock, playback_manager, menu_manager, playlist_manager, radio_manager, tidal_manager, qobuz_manager):
        self.display_manager = display_manager
        self.clock = clock
        self.playback_manager = playback_manager
        self.menu_manager = menu_manager
        self.playlist_manager = playlist_manager
        self.radio_manager = radio_manager
        self.tidal_manager = tidal_manager
        self.qobuz_manager = qobuz_manager

        # Initialize logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)  # Set to INFO or DEBUG as needed
        self.logger.info("ModeManager initialized.")

        # Set up transitions and states
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
        self.machine.add_transition(trigger='to_qobuz', source='*', dest='qobuz')
        self.machine.add_transition(trigger='to_clock', source='*', dest='clock')

        self.on_mode_change_callbacks = []
        self.lock = threading.Lock()

        # Explicitly call 'enter_clock' to ensure initial state is set
        self.enter_clock(event=None)

    def add_on_mode_change_callback(self, callback):
        with self.lock:
            if callable(callback):
                self.on_mode_change_callbacks.append(callback)
                self.logger.debug(f"ModeManager: Added mode change callback: {callback}")
            else:
                self.logger.warning("ModeManager: Provided callback is not callable.")

    def notify_mode_change(self, current_mode):
        """Notify listeners of the mode change."""
        with self.lock:
            self.logger.debug(f"ModeManager: Notifying mode change to: {current_mode}")
            for callback in self.on_mode_change_callbacks:
                try:
                    callback(current_mode)
                    self.logger.debug(f"ModeManager: Callback {callback} executed successfully.")
                except Exception as e:
                    self.logger.error(f"ModeManager: Error in callback {callback}: {e}")

            # Notify DisplayManager directly
            if hasattr(self.display_manager, "notify_mode_change"):
                self.display_manager.notify_mode_change(current_mode)
                self.logger.debug("ModeManager: Notified DisplayManager of mode change.")

    # Define all 'on_enter' methods with 'event=None' to make 'event' optional
    def enter_playback(self, event=None):
        self.logger.info("ModeManager: Entering playback mode.")
        self.clock.stop()  # Stop clock mode if active
        self.menu_manager.stop_mode()  # Stop other modes if necessary

        # Start playback display through PlaybackManager
        self.playback_manager.start_mode()
        self.notify_mode_change('playback')

    def enter_menu(self, event=None):
        self.logger.info("ModeManager: Entering menu mode.")
        self.clock.stop()
        self.playback_manager.stop_mode()
        self.radio_manager.stop_mode()
        self.playlist_manager.stop_mode()
        self.tidal_manager.stop_mode()
        self.qobuz_manager.stop_mode()
        self.menu_manager.start_mode()
        self.notify_mode_change('menu')

    def enter_webradio(self, event=None):
        self.logger.info("ModeManager: Entering webradio mode.")
        self.clock.stop()
        self.playback_manager.stop_mode()
        self.menu_manager.stop_mode()
        self.playlist_manager.stop_mode()
        self.tidal_manager.stop_mode()
        self.qobuz_manager.stop_mode()
        self.radio_manager.start_mode()
        self.notify_mode_change('webradio')

    def enter_playlist(self, event=None):
        self.logger.info("ModeManager: Entering playlist mode.")
        self.clock.stop()
        self.playback_manager.stop_mode()
        self.menu_manager.stop_mode()
        self.radio_manager.stop_mode()
        self.tidal_manager.stop_mode()
        self.qobuz_manager.stop_mode()
        self.playlist_manager.start_mode()
        self.notify_mode_change('playlist')

    def enter_favourites(self, event=None):
        self.logger.info("ModeManager: Entering favourites mode.")
        self.clock.stop()
        self.playback_manager.stop_mode()
        self.menu_manager.stop_mode()
        self.radio_manager.stop_mode()
        self.playlist_manager.stop_mode()
        self.tidal_manager.stop_mode()
        self.qobuz_manager.stop_mode()
        # Implement favourites mode logic here
        self.notify_mode_change('favourites')

    def enter_tidal(self, event=None):
        self.logger.info("ModeManager: Entering tidal mode.")
        self.clock.stop()
        self.playback_manager.stop_mode()
        self.menu_manager.stop_mode()
        self.radio_manager.stop_mode()
        self.playlist_manager.stop_mode()
        self.qobuz_manager.stop_mode()
        self.tidal_manager.start_mode()
        self.notify_mode_change('tidal')

    def enter_qobuz(self, event=None):
        self.logger.info("ModeManager: Entering qobuz mode.")
        self.clock.stop()
        self.playback_manager.stop_mode()
        self.menu_manager.stop_mode()
        self.radio_manager.stop_mode()
        self.playlist_manager.stop_mode()
        self.tidal_manager.stop_mode()
        self.qobuz_manager.start_mode()
        self.notify_mode_change('qobuz')

    def enter_clock(self, event=None):
        self.logger.info("ModeManager: Entering clock mode.")
        self.playback_manager.stop_mode()  # Stop playback display
        self.menu_manager.stop_mode()
        self.radio_manager.stop_mode()
        self.playlist_manager.stop_mode()
        self.tidal_manager.stop_mode()
        self.qobuz_manager.stop_mode()
        self.clock.start()  # Start clock display
        self.notify_mode_change('clock')

    def process_state_change(self, state):
        status = state.get("status", "")
        self.logger.debug(f"ModeManager: Processing state change, Volumio status: {status}")

        if status == "play":
            self.to_playback()  # Switch to playback mode if playing
        elif status in ["pause", "stop"]:
            self.to_clock()  # Return to clock mode if paused or stopped
