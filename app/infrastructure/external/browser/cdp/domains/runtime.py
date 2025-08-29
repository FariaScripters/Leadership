from typing import Dict, Any, Optional, List
from .base import CDPDomain

class RuntimeDomain(CDPDomain):
    """CDP Runtime domain implementation"""
    
    async def enable(self):
        """Enable runtime domain events"""
        await self.execute_command("Runtime.enable")
        
    async def evaluate(self, expression: str, await_promise: bool = False,
                      return_by_value: bool = True) -> Dict[str, Any]:
        """Evaluate JavaScript expression
        
        Args:
            expression: Expression to evaluate
            await_promise: Whether to await any resulting promises
            return_by_value: Whether to return by value
            
        Returns:
            Evaluation result
        """
        params = {
            "expression": expression,
            "returnByValue": return_by_value,
            "awaitPromise": await_promise
        }
        return await self.execute_command("Runtime.evaluate", params)
        
    async def call_function_on(self, function_declaration: str, object_id: str,
                             arguments: Optional[List[Dict[str, Any]]] = None,
                             await_promise: bool = False) -> Dict[str, Any]:
        """Call function on object
        
        Args:
            function_declaration: Function to call
            object_id: Object ID
            arguments: Function arguments
            await_promise: Whether to await any resulting promises
            
        Returns:
            Function result
        """
        params = {
            "functionDeclaration": function_declaration,
            "objectId": object_id,
            "awaitPromise": await_promise
        }
        if arguments:
            params["arguments"] = arguments
        return await self.execute_command("Runtime.callFunctionOn", params)
