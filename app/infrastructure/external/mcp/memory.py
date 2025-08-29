from typing import Dict, Any, List, Optional
from app.infrastructure.external.mcp.sequential_thinking import MCPServer
import json
import logging

logger = logging.getLogger(__name__)

class MemoryMCP(MCPServer):
    """Memory MCP implementation for storing and retrieving contextual information"""
    
    def __init__(self):
        super().__init__("memory")
        
    async def store_memory(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store a memory
        
        Args:
            key: Memory key
            value: Memory value
            metadata: Optional metadata about the memory
            
        Returns:
            Success status
        """
        request = {
            "type": "store",
            "key": key,
            "value": value,
            "metadata": metadata or {}
        }
        
        try:
            response = await self.send_request(request)
            return response.get("success", False)
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            return False
            
    async def retrieve_memory(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a memory
        
        Args:
            key: Memory key
            
        Returns:
            Memory data if found, None otherwise
        """
        request = {
            "type": "retrieve",
            "key": key
        }
        
        try:
            response = await self.send_request(request)
            return response.get("memory")
        except Exception as e:
            logger.error(f"Error retrieving memory: {str(e)}")
            return None
            
    async def search_memories(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories by similarity
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching memories
        """
        request = {
            "type": "search",
            "query": query,
            "limit": limit
        }
        
        try:
            response = await self.send_request(request)
            return response.get("results", [])
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return []
