from typing import Optional, Dict, Any
import asyncio
import json
import logging
import aiohttp
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class CDPConnectionManager:
    """Chrome DevTools Protocol connection manager"""
    
    def __init__(self):
        self.settings = get_settings()
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self._message_id = 0
        self._callbacks: Dict[int, asyncio.Future] = {}
        self._event_handlers: Dict[str, callable] = {}
        
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
            await self.send_command("Network.enable")
            await self.send_command("Page.enable")
            await self.send_command("Runtime.enable")
            
            logger.info("Connected to Chrome DevTools Protocol")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to CDP: {str(e)}")
            await self.disconnect()
            return False
            
    async def disconnect(self):
        """Disconnect from Chrome DevTools Protocol"""
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
