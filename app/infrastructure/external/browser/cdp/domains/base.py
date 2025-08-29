from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

class CDPDomain(ABC):
    """Base class for CDP domains"""
    
    def __init__(self, connection):
        self.connection = connection
        
    async def execute_command(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute CDP command
        
        Args:
            method: Command method name
            params: Command parameters
            
        Returns:
            Command result
        """
        return await self.connection.send_command(method, params)
        
    def add_event_handler(self, event: str, handler: callable):
        """Add event handler
        
        Args:
            event: Event name
            handler: Event handler function
        """
        self.connection.on_event(event, handler)
