from typing import Optional, Dict, Any, List
import asyncio
import json
import logging
import aiohttp
from app.core.config import get_settings
from .cdp.domains.page import PageDomain
from .cdp.domains.network import NetworkDomain
from .cdp.domains.runtime import RuntimeDomain
from .cdp.domains.dom import DOMDomain
from .cdp.session import CDPSession

logger = logging.getLogger(__name__)

class CDPConnectionManager:
    """Chrome DevTools Protocol connection manager with domain support"""
    
    def __init__(self):
        self.settings = get_settings()
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self._message_id = 0
        self._callbacks: Dict[int, asyncio.Future] = {}
        self._event_handlers: Dict[str, callable] = {}
        
        # Initialize domains
        self.page = PageDomain(self)
        self.network = NetworkDomain(self)
        self.runtime = RuntimeDomain(self)
        self.dom = DOMDomain(self)
        
        # Store active sessions
        self._sessions: Dict[str, 'CDPSession'] = {}
        
    @property
    def message_id(self) -> int:
        """Get next message ID"""
        self._message_id += 1
        return self._message_id
        
    async def connect(self) -> bool:
        """Connect to Chrome DevTools Protocol endpoint
        
        Returns:
            bool: Connection success
        """
        try:
            if self.ws:
                await self.disconnect()
                
            self.session = aiohttp.ClientSession()
            self.ws = await self.session.ws_connect(self.settings.chrome_ws_endpoint)
            
            # Start message handler
            asyncio.create_task(self._handle_messages())
            
            # Enable necessary domains
            await self.network.enable()
            await self.page.enable()
            await self.runtime.enable()
            await self.dom.enable()
            
            # Enable target tracking
            await self.send_command("Target.setDiscoverTargets", {"discover": True})
            
            # Set up target attached/detached handlers
            self.on_event("Target.targetCreated", self._handle_target_created)
            self.on_event("Target.targetDestroyed", self._handle_target_destroyed)
            
            logger.info("Connected to Chrome DevTools Protocol")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to CDP: {str(e)}")
            await self.disconnect()
            return False
            
    async def disconnect(self):
        """Disconnect from Chrome DevTools Protocol"""
        # Detach from all targets
        for session in self._sessions.values():
            try:
                await session.detach()
            except:
                pass
        self._sessions.clear()
        
        if self.ws:
            await self.ws.close()
            self.ws = None
            
        if self.session:
            await self.session.close()
            self.session = None
            
        # Clear callbacks
        for future in self._callbacks.values():
            if not future.done():
                future.cancel()
        self._callbacks.clear()
        
    async def _handle_target_created(self, params: Dict[str, Any]):
        """Handle new target creation"""
        target_info = params["targetInfo"]
        
        # Attach to target
        response = await self.send_command(
            "Target.attachToTarget",
            {"targetId": target_info["targetId"], "flatten": True}
        )
        
        session_id = response["sessionId"]
        session = CDPSession(self, target_info["targetId"], session_id)
        self._sessions[session_id] = session
        
        logger.info(f"Attached to target: {target_info['url']} ({session_id})")
        
    async def _handle_target_destroyed(self, params: Dict[str, Any]):
        """Handle target destruction"""
        target_id = params["targetId"]
        sessions_to_remove = [
            session_id for session_id, session in self._sessions.items()
            if session.target_id == target_id
        ]
        
        for session_id in sessions_to_remove:
            session = self._sessions.pop(session_id)
            try:
                await session.detach()
            except:
                pass
                
        logger.info(f"Target destroyed: {target_id}")
        
    async def create_target(self, url: str = "about:blank") -> CDPSession:
        """Create new target
        
        Args:
            url: Initial URL
            
        Returns:
            CDP session for new target
        """
        response = await self.send_command("Target.createTarget", {"url": url})
        target_id = response["targetId"]
        
        # Wait for session to be created
        for _ in range(100):  # Wait up to 10 seconds
            session = next(
                (s for s in self._sessions.values() if s.target_id == target_id),
                None
            )
            if session:
                return session
            await asyncio.sleep(0.1)
            
        raise Exception("Failed to create target session")
        
    async def send_command(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send command to Chrome DevTools Protocol
        
        Args:
            method: Command method name
            params: Command parameters
            
        Returns:
            Command result
        """
        if not self.ws:
            raise Exception("Not connected to CDP")
            
        message_id = self.message_id
        message = {
            "id": message_id,
            "method": method,
            "params": params or {}
        }
        
        # Create future for response
        future = asyncio.Future()
        self._callbacks[message_id] = future
        
        # Send message
        await self.ws.send_str(json.dumps(message))
        
        try:
            # Wait for response
            response = await future
            return response
        finally:
            # Clean up callback
            self._callbacks.pop(message_id, None)
            
    def on_event(self, event: str, callback: callable):
        """Register event handler
        
        Args:
            event: Event name
            callback: Event handler function
        """
        self._event_handlers[event] = callback
        
    async def _handle_messages(self):
        """Handle incoming WebSocket messages"""
        if not self.ws:
            return
            
        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    
                    # Handle command response
                    if "id" in data:
                        message_id = data["id"]
                        future = self._callbacks.get(message_id)
                        if future and not future.done():
                            if "error" in data:
                                future.set_exception(Exception(data["error"]["message"]))
                            else:
                                future.set_result(data.get("result", {}))
                                
                    # Handle event
                    elif "method" in data:
                        event = data["method"]
                        handler = self._event_handlers.get(event)
                        if handler:
                            try:
                                await handler(data.get("params", {}))
                            except Exception as e:
                                logger.error(f"Error in event handler for {event}: {str(e)}")
                                
        except Exception as e:
            logger.error(f"Error handling CDP messages: {str(e)}")
        finally:
            await self.disconnect()
