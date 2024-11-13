# src/commands/volume_down_command.py
from src.commands.base_command import BaseCommand

class VolumeDownCommand(BaseCommand):
    def __init__(self, volumio_listener, decrement=5):
        self.volumio_listener = volumio_listener
        self.decrement = decrement

    def execute(self):
        self.volumio_listener.adjust_volume(-self.decrement)

