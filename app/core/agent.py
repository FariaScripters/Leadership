from typing import Dict, Any, Optional, List, Type
from abc import ABC, abstractmethod
import asyncio
import logging
import uuid
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ToolType(Enum):
    """Tool types supported by the agent"""
    BROWSER = "browser"
    TERMINAL = "terminal"
    FILE = "file"
    WEB = "web"
    MCP = "mcp"
    CUSTOM = "custom"

@dataclass
class ToolCapability:
    """Tool capability descriptor"""
    name: str
    type: ToolType
    description: str
    private: bool = True
    requires_auth: bool = False
    sandbox: bool = True
    
@dataclass
class ToolContext:
    """Context for tool execution"""
    user_id: str
    session_id: str
    sandbox_id: str
    workspace: str
    tool_id: str
    params: Dict[str, Any]

class Tool(ABC):
    """Base class for all tools"""
    
    @abstractmethod
    def get_capabilities(self) -> ToolCapability:
        """Get tool capabilities"""
        pass
        
    @abstractmethod
    async def initialize(self, context: ToolContext):
        """Initialize tool with context"""
        pass
        
    @abstractmethod
    async def execute(self, command: str, params: Dict[str, Any]) -> Any:
        """Execute tool command"""
        pass
        
    @abstractmethod
    async def cleanup(self):
        """Cleanup tool resources"""
        pass

class SandboxManager:
    """Manages tool sandboxes"""
    
    def __init__(self):
        self._sandboxes: Dict[str, 'Sandbox'] = {}
        
    async def create_sandbox(self, user_id: str, session_id: str) -> 'Sandbox':
        """Create new sandbox"""
        sandbox_id = str(uuid.uuid4())
        sandbox = Sandbox(sandbox_id, user_id, session_id)
        self._sandboxes[sandbox_id] = sandbox
        await sandbox.initialize()
        return sandbox
        
    async def get_sandbox(self, sandbox_id: str) -> Optional['Sandbox']:
        """Get existing sandbox"""
        return self._sandboxes.get(sandbox_id)
        
    async def cleanup_sandbox(self, sandbox_id: str):
        """Cleanup sandbox"""
        if sandbox_id in self._sandboxes:
            await self._sandboxes[sandbox_id].cleanup()
            del self._sandboxes[sandbox_id]

class Sandbox:
    """Tool sandbox environment"""
    
    def __init__(self, sandbox_id: str, user_id: str, session_id: str):
        self.sandbox_id = sandbox_id
        self.user_id = user_id
        self.session_id = session_id
        self.workspace = f"/tmp/workspace/{sandbox_id}"
        self._tools: Dict[str, Tool] = {}
        self._running = False
        
    async def initialize(self):
        """Initialize sandbox"""
        import os
        os.makedirs(self.workspace, exist_ok=True)
        self._running = True
        
    async def add_tool(self, tool: Tool) -> str:
        """Add tool to sandbox"""
        if not self._running:
            raise RuntimeError("Sandbox not running")
            
        tool_id = str(uuid.uuid4())
        context = ToolContext(
            user_id=self.user_id,
            session_id=self.session_id,
            sandbox_id=self.sandbox_id,
            workspace=self.workspace,
            tool_id=tool_id,
            params={}
        )
        
        await tool.initialize(context)
        self._tools[tool_id] = tool
        return tool_id
        
    async def execute_tool(
        self,
        tool_id: str,
        command: str,
        params: Dict[str, Any]
    ) -> Any:
        """Execute tool command"""
        if not self._running:
            raise RuntimeError("Sandbox not running")
            
        tool = self._tools.get(tool_id)
        if not tool:
            raise ValueError(f"Tool {tool_id} not found")
            
        return await tool.execute(command, params)
        
    async def cleanup(self):
        """Cleanup sandbox"""
        self._running = False
        
        # Cleanup tools
        for tool in self._tools.values():
            try:
                await tool.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up tool: {str(e)}")
                
        # Cleanup workspace
        import shutil
        shutil.rmtree(self.workspace, ignore_errors=True)
        
        self._tools.clear()

class AgentSession:
    """Agent session for a user"""
    
    def __init__(self, user_id: str):
        self.session_id = str(uuid.uuid4())
        self.user_id = user_id
        self.created_at = datetime.utcnow()
        self.sandbox_manager = SandboxManager()
        self.current_sandbox: Optional[Sandbox] = None
        
    async def create_sandbox(self) -> Sandbox:
        """Create new sandbox for session"""
        self.current_sandbox = await self.sandbox_manager.create_sandbox(
            self.user_id,
            self.session_id
        )
        return self.current_sandbox
        
    async def cleanup(self):
        """Cleanup session"""
        if self.current_sandbox:
            await self.sandbox_manager.cleanup_sandbox(
                self.current_sandbox.sandbox_id
            )
            self.current_sandbox = None

class AgentManager:
    """Manages agent sessions"""
    
    def __init__(self):
        self._sessions: Dict[str, AgentSession] = {}
        
    async def create_session(self, user_id: str) -> AgentSession:
        """Create new agent session"""
        session = AgentSession(user_id)
        self._sessions[session.session_id] = session
        return session
        
    async def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Get existing session"""
        return self._sessions.get(session_id)
        
    async def cleanup_session(self, session_id: str):
        """Cleanup session"""
        if session_id in self._sessions:
            await self._sessions[session_id].cleanup()
            del self._sessions[session_id]
