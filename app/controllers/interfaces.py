from abc import ABC, abstractmethod

class IModeController(ABC):
    @abstractmethod
    def get_current_mode(self):
        pass

    @abstractmethod
    def request_mode_change(self, new_mode, confirm=False):
        pass

class IPumpController(ABC):
    @abstractmethod
    def set_manual_pump(self, running):
        pass

    @abstractmethod
    def get_system_state(self):
        pass
    
    @abstractmethod
    def set_distribution_pump(self, state):
        """Control distribution pump state
        
        Args:
            state (bool): True to turn on, False to turn off
        """
        pass