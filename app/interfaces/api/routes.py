from fastapi import APIRouter, HTTPException
from app.infrastructure.external.llm.gemini_llm import GeminiLLM
from app.infrastructure.external.mcp.sequential_thinking import SequentialThinkingMCP
from app.infrastructure.external.mcp.memory import MemoryMCP
from app.infrastructure.external.mcp.playwright import PlaywrightMCP
from app.infrastructure.external.mcp.task_orchestrator import TaskOrchestratorMCP
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

router = APIRouter()
llm = GeminiLLM()
sequential_thinking_mcp = SequentialThinkingMCP()
memory_mcp = MemoryMCP()
playwright_mcp = PlaywrightMCP()
task_orchestrator_mcp = TaskOrchestratorMCP()

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]

class ThoughtRequest(BaseModel):
    context: str
    query: str

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint that uses Gemini for responses
    
    Args:
        request: Chat request with messages
    """
    try:
        response = await llm.ask(request.messages)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/think")
async def think(request: ThoughtRequest):
    """Sequential thinking endpoint"""
    try:
        thoughts = await sequential_thinking_mcp.process_thought(request.context, request.query)
        return {"thoughts": thoughts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MemoryRequest(BaseModel):
    key: str
    value: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None
    query: Optional[str] = None
    limit: Optional[int] = 10

@router.post("/memory/store")
async def store_memory(request: MemoryRequest):
    """Store a memory"""
    try:
        success = await memory_mcp.store_memory(request.key, request.value, request.metadata)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/{key}")
async def get_memory(key: str):
    """Retrieve a memory"""
    try:
        memory = await memory_mcp.retrieve_memory(key)
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        return memory
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memory/search")
async def search_memories(request: MemoryRequest):
    """Search memories"""
    try:
        results = await memory_mcp.search_memories(request.query, request.limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class BrowserRequest(BaseModel):
    url: Optional[str] = None
    selector: Optional[str] = None
    text: Optional[str] = None
    wait_for_load: Optional[bool] = True

@router.post("/browser/navigate")
async def navigate(request: BrowserRequest):
    """Navigate to a URL"""
    try:
        result = await playwright_mcp.navigate(request.url, request.wait_for_load)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/browser/click")
async def click(request: BrowserRequest):
    """Click an element"""
    try:
        result = await playwright_mcp.click(request.selector)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/browser/type")
async def type_text(request: BrowserRequest):
    """Type text into an element"""
    try:
        result = await playwright_mcp.type_text(request.selector, request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/browser/text")
async def get_text(selector: str):
    """Get element text"""
    try:
        text = await playwright_mcp.get_text(selector)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TaskRequest(BaseModel):
    task_type: Optional[str] = None
    task_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    tasks: Optional[List[Dict[str, Any]]] = None
    dependencies: Optional[List[Dict[str, Any]]] = None
    workflow_id: Optional[str] = None

@router.post("/tasks/create")
async def create_task(request: TaskRequest):
    """Create a new task"""
    try:
        task_id = await task_orchestrator_mcp.create_task(request.task_type, request.parameters)
        return {"task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Get task status"""
    try:
        status = await task_orchestrator_mcp.get_task_status(task_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a task"""
    try:
        success = await task_orchestrator_mcp.cancel_task(task_id)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks")
async def list_tasks(status: Optional[str] = None):
    """List tasks"""
    try:
        tasks = await task_orchestrator_mcp.list_tasks(status)
        return {"tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflows/create")
async def create_workflow(request: TaskRequest):
    """Create a new workflow"""
    try:
        workflow_id = await task_orchestrator_mcp.create_workflow(request.tasks, request.dependencies)
        return {"workflow_id": workflow_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get workflow status"""
    try:
        status = await task_orchestrator_mcp.get_workflow_status(workflow_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
