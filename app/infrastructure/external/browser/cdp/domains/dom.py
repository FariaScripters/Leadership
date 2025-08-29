from typing import Dict, Any, Optional, List
from .base import CDPDomain

class DOMDomain(CDPDomain):
    """CDP DOM domain implementation"""
    
    async def enable(self):
        """Enable DOM domain events"""
        await self.execute_command("DOM.enable")
        
    async def get_document(self) -> Dict[str, Any]:
        """Get document root node"""
        return await self.execute_command("DOM.getDocument")
        
    async def query_selector(self, node_id: int, selector: str) -> Optional[int]:
        """Query selector in node
        
        Args:
            node_id: Node ID
            selector: CSS selector
            
        Returns:
            Node ID of found element or None
        """
        result = await self.execute_command("DOM.querySelector", {
            "nodeId": node_id,
            "selector": selector
        })
        return result.get("nodeId")
        
    async def get_outer_html(self, node_id: int) -> str:
        """Get node outer HTML
        
        Args:
            node_id: Node ID
            
        Returns:
            Outer HTML
        """
        result = await self.execute_command("DOM.getOuterHTML", {"nodeId": node_id})
        return result.get("outerHTML", "")
