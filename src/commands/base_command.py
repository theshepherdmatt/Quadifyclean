# src/commands/base_command.py
from abc import ABC, abstractmethod

class BaseCommand(ABC):
    @abstractmethod
    def execute(self):
        pass

