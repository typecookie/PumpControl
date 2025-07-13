# app/controllers/__init__.py

class Controller:
    _instances = {}
    
    @classmethod
    def get_instance(cls):
        if cls not in cls._instances:
            cls._instances[cls] = cls()
        return cls._instances[cls]
    
    @classmethod
    def initialize_all(cls):
        """Initialize all controllers"""
        from .pump_controller import PumpController
        
        # Initialize each controller
        PumpController.get_instance().start()
    
    @classmethod
    def cleanup_all(cls):
        """Cleanup all controllers"""
        for controller in cls._instances.values():
            if hasattr(controller, 'stop'):
                controller.stop()