from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, Tuple

class IModeController(ABC):
    @abstractmethod
    def get_current_mode(self) -> str:
        """Get the current system mode
        
        Returns:
            str: Current mode (SUMMER, WINTER, or CHANGEOVER)
        """
        pass

    @abstractmethod
    def request_mode_change(self, new_mode: str, confirm: bool = False) -> Union[Dict[str, Any], Tuple[Dict[str, Any], int]]:
        """Request a mode change
        
        Args:
            new_mode: The mode to change to (SUMMER, WINTER, or CHANGEOVER)
            confirm: Whether this is a confirmation of a previous request
            
        Returns:
            Union[Dict[str, Any], Tuple[Dict[str, Any], int]]: Response data and optional status code
        """
        pass

class IPumpController(ABC):
    @abstractmethod
    def set_manual_pump(self, running: bool) -> Dict[str, Any]:
        """Control manual pump operation
        
        Args:
            running: True to turn on, False to turn off
            
        Returns:
            Dict[str, Any]: Status response
        """
        pass

    @abstractmethod
    def get_system_state(self) -> Dict[str, Any]:
        """Get current system state
        
        Returns:
            Dict[str, Any]: Complete system state
        """
        pass
    
    @abstractmethod
    def set_distribution_pump(self, state: bool) -> Dict[str, Any]:
        """Control distribution pump state
        
        Args:
            state: True to turn on, False to turn off
            
        Returns:
            Dict[str, Any]: Status response
        """
        pass