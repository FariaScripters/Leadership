from typing import Dict, Any, Optional, List, Callable, Union, TypeVar
import asyncio
import json
import logging
import aiohttp
import re
from dataclasses import dataclass
from asyncio import Future, Task

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class CDPCommand:
    """Represents a CDP command with its metadata"""
    id: int
    method: str
    session_id: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    
class CDPError(Exception):
    """CDP specific error"""
    def __init__(self, message: str, code: Optional[int] = None, data: Any = None):
        super().__init__(message)
        self.code = code
        self.data = data

class CDPConnection:
    """Enhanced CDP connection with better error handling and message routing"""
    
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self._message_id = 0
        self._callbacks: Dict[int, Future] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._sessions: Dict[str, 'CDPSession'] = {}
        self._closed = False
        self._ws_messages: asyncio.Queue = asyncio.Queue()
        self._message_task: Optional[Task] = None
        
    @property
    def next_message_id(self) -> int:
        """Get next message ID"""
        self._message_id += 1
        return self._message_id
        
    async def connect(self) -> bool:
        """Connect to CDP endpoint"""
        try:
            if self.ws:
                await self.disconnect()
                
            self.session = aiohttp.ClientSession()
            self.ws = await self.session.ws_connect(
                self.ws_url,
                max_msg_size=0,  # No limit on message size
                timeout=30
            )
            
            # Start message handler
            self._message_task = asyncio.create_task(self._handle_messages())
            
            logger.info(f"Connected to CDP endpoint: {self.ws_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to CDP: {str(e)}")
            await self.disconnect()
            return False
            
    async def disconnect(self):
        """Disconnect from CDP endpoint"""
        self._closed = True
        
        # Cancel message handler
        if self._message_task:
            self._message_task.cancel()
            try:
                await self._message_task
            except asyncio.CancelledError:
                pass
            self._message_task = None
            
        # Close websocket
        if self.ws:
            await self.ws.close()
            self.ws = None
            
        # Close session
        if self.session:
            await self.session.close()
            self.session = None
            
        # Clear state
        self._callbacks.clear()
        self._event_handlers.clear()
        self._sessions.clear()
        
    async def send_command(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        timeout: float = 30
    ) -> Dict[str, Any]:
        """Send CDP command with timeout
        
        Args:
            method: Command method
            params: Command parameters
            session_id: Session ID for target
            timeout: Command timeout in seconds
            
        Returns:
            Command result
            
        Raises:
            CDPError: On protocol error
            TimeoutError: On timeout
            ConnectionError: On connection issues
        """
        if not self.ws:
            raise ConnectionError("Not connected to CDP endpoint")
            
        command = CDPCommand(
            id=self.next_message_id,
            method=method,
            params=params,
            session_id=session_id
        )
        
        # Create future for response
        future = asyncio.Future()
        self._callbacks[command.id] = future
        
        try:
            # Send command
            message = {
                "id": command.id,
                "method": command.method
            }
            if command.params:
                message["params"] = command.params
            if command.session_id:
                message["sessionId"] = command.session_id
                
            await self.ws.send_str(json.dumps(message))
            
            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout)
            
            if "error" in response:
                error = response["error"]
                raise CDPError(
                    error.get("message", "Unknown error"),
                    error.get("code"),
                    error.get("data")
                )
                
            return response.get("result", {})
            
        finally:
            self._callbacks.pop(command.id, None)
            
    def on(self, event: str, handler: Callable):
        """Add event handler
        
        Args:
            event: Event name
            handler: Event handler function
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
        
    def off(self, event: str, handler: Optional[Callable] = None):
        """Remove event handler
        
        Args:
            event: Event name
            handler: Event handler to remove, or None to remove all
        """
        if event in self._event_handlers:
            if handler:
                self._event_handlers[event].remove(handler)
                if not self._event_handlers[event]:
                    del self._event_handlers[event]
            else:
                del self._event_handlers[event]
                
    async def _handle_messages(self):
        """Handle incoming websocket messages"""
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
                            future.set_result(data)
                            
                    # Handle event
                    elif "method" in data:
                        event = data["method"]
                        params = data.get("params", {})
                        session_id = data.get("sessionId")
                        
                        # Route event to session
                        if session_id and session_id in self._sessions:
                            await self._sessions[session_id]._on_event(event, params)
                            
                        # Handle connection-level events
                        handlers = self._event_handlers.get(event, [])
                        for handler in handlers:
                            try:
                                if asyncio.iscoroutinefunction(handler):
                                    await handler(params)
                                else:
                                    handler(params)
                            except Exception as e:
                                logger.error(f"Error in event handler for {event}: {str(e)}")
                                
        except Exception as e:
            if not self._closed:
                logger.error(f"Error handling CDP messages: {str(e)}")
                await self.disconnect()
