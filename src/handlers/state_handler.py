# src/handlers/state_handler.py

import logging

class StateHandler:
    def __init__(self, volumio_listener, mode_manager):
        self.volumio_listener = volumio_listener
        self.mode_manager = mode_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)  # Set to desired level (DEBUG/INFO/etc.)
        
        self.register_listeners()

    def register_listeners(self):
        # Register as a signal handler
        self.volumio_listener.register_state_change_callback(self.on_volumio_state_change)
        # Register as a mode change callback
        self.mode_manager.add_on_mode_change_callback(self.on_mode_change)

    def on_volumio_state_change(self, sender, **kwargs):
        state = kwargs.get('state')
        self.logger.info("StateHandler: Received state change.")
        # Handle the state change using the state data
        if state:
            self.mode_manager.process_state_change(state)

    def on_mode_change(self, current_mode):
        self.logger.info(f"StateHandler: Mode changed to {current_mode}")
        # Implement any additional logic needed when mode changes
        # For example, updating the display or triggering other actions
