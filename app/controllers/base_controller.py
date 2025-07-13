class Controller:
    def __init__(self):
        self._initialized = False
        self._init()
        self._initialized = True
    
    def _init(self):
        """Override this method for controller-specific initialization"""
        pass

    def cleanup(self):
        """Override this method for controller-specific cleanup"""
        pass