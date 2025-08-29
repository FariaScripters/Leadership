from typing import Dict, Any, Optional

class CDPSession:
    """Represents a CDP session for a target"""
    
    def __init__(self, connection, target_id: str, session_id: str):
        self.connection = connection
        self.target_id = target_id
        self.session_id = session_id
        
    async def send_command(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send command in this session's context"""
        params = params or {}
        params["sessionId"] = self.session_id
        return await self.connection.send_command(method, params)
        
    async def detach(self):
        """Detach from target"""
        await self.connection.send_command("Target.detachFromTarget", {"sessionId": self.session_id})
