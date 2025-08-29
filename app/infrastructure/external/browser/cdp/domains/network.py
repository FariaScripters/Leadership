from typing import Dict, Any, Optional, List
from .base import CDPDomain

class NetworkDomain(CDPDomain):
    """CDP Network domain implementation"""
    
    async def enable(self, max_resource_buffer_size: Optional[int] = None):
        """Enable network domain events
        
        Args:
            max_resource_buffer_size: Buffer size in bytes
        """
        params = {}
        if max_resource_buffer_size:
            params["maxResourceBufferSize"] = max_resource_buffer_size
        await self.execute_command("Network.enable", params)
        
    async def disable(self):
        """Disable network domain events"""
        await self.execute_command("Network.disable")
        
    async def set_request_interception(self, patterns: List[Dict[str, Any]]):
        """Enable request interception
        
        Args:
            patterns: Interception patterns
        """
        await self.execute_command("Network.setRequestInterception", {"patterns": patterns})
        
    async def continue_intercepted_request(self, request_id: str, **kwargs):
        """Continue intercepted request
        
        Args:
            request_id: Interception ID
            **kwargs: Optional parameters (url, method, postData, headers)
        """
        params = {"interceptionId": request_id, **kwargs}
        await self.execute_command("Network.continueInterceptedRequest", params)
        
    async def get_response_body(self, request_id: str) -> Dict[str, Any]:
        """Get response body
        
        Args:
            request_id: Request ID
            
        Returns:
            Response body and base64 encoding flag
        """
        return await self.execute_command("Network.getResponseBody", {"requestId": request_id})
