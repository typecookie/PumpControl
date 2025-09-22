
from abc import ABC, abstractmethod
from typing import Dict, Any
from app.utils.gpio_utils import GPIOManager
from app.utils.config_utils import (
    SUMMER_HIGH, SUMMER_LOW, SUMMER_EMPTY,
    WINTER_HIGH, WINTER_LOW
)

class BaseModeHandler(ABC):
    def __init__(self, pump_controller, notification_service):
        self.pump_controller = pump_controller
        self.notification_service = notification_service

    def get_tank_states(self) -> dict:
        """Get current states of all tank sensors"""
        return {
            'summer': {
                'high': GPIOManager.get_sensor_state(SUMMER_HIGH),
                'low': GPIOManager.get_sensor_state(SUMMER_LOW),
                'empty': GPIOManager.get_sensor_state(SUMMER_EMPTY)
            },
            'winter': {
                'high': GPIOManager.get_sensor_state(WINTER_HIGH),
                'low': GPIOManager.get_sensor_state(WINTER_LOW)
            }
        }

    @abstractmethod
    def handle(self, tank_state) -> None:
        """Handle mode-specific logic"""
        pass

    @abstractmethod
    def on_mode_enter(self) -> None:
        """Called when entering this mode"""
        pass

    @abstractmethod
    def on_mode_exit(self) -> None:
        """Called when exiting this mode"""
        pass