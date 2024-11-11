# src/commands/volume_up_command.py
from base_command import BaseCommand

class VolumeUpCommand(BaseCommand):
    def __init__(self, volumio_listener, increment=5):
        self.volumio_listener = volumio_listener
        self.increment = increment

    def execute(self):
        self.volumio_listener.adjust_volume(self.increment)

