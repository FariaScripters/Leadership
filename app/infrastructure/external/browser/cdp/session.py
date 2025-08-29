from typing import Dict, Any, Optional, List, Callable, Union, Protocol
import asyncio
import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class CDPConnectionProtocol(Protocol):
    """Protocol defining CDP connection interface"""
    async def send_command(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        timeout: float = 30
    ) -> Dict[str, Any]: ...

@dataclass
class TargetInfo:
    """Target information"""
    target_id: str
    type: str
    title: str
    url: str
    attached: bool
    browser_context_id: Optional[str] = None

class CDPSession:
    """Enhanced CDP session with event handling"""
    """Represents a CDP session for a target"""
    
    def __init__(self, connection: CDPConnectionProtocol, target_info: TargetInfo, session_id: str):
        self.connection = connection
        self.target_info = target_info
        self.session_id = session_id
        self._event_handlers: Dict[str, List[Callable]] = {}
        
    async def send_command(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send command in this session's context"""
        params = params or {}
        params["sessionId"] = self.session_id
        return await self.connection.send_command(method, params)
        
    async def detach(self):
        """Detach from target"""
        await self.connection.send_command("Target.detachFromTarget", {"sessionId": self.session_id})
