class BaseAgent:
    """Base Agent class representing a generic agent in the system"""
    
    def __init__(self, *args, **kwargs):
        pass

    def execute(self, *args, **kwargs):
        """Execute the agent logic"""
        raise NotImplementedError("Subclasses must implement execute method")
