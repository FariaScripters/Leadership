import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.infrastructure.external.mcp.sequential_thinking import SequentialThinkingMCP

@pytest.fixture
async def mcp_server():
    server = SequentialThinkingMCP()
    yield server
    await server.stop()

@pytest.mark.skip_mcp
@pytest.mark.asyncio
async def test_process_thought_success(mcp_server):
    # Mock process
    process_mock = AsyncMock()
    process_mock.stdin = AsyncMock()
    process_mock.stdout = AsyncMock()
    
    # Mock response
    response = b'{"thoughts": ["Step 1", "Step 2", "Step 3"]}\n'
    process_mock.stdout.readline.return_value = response
    
    # Mock process creation
    with patch('asyncio.create_subprocess_exec', return_value=process_mock):
        # Test thought processing
        thoughts = await mcp_server.process_thought(
            context="Test context",
            query="What are the steps?"
        )
        
        # Verify results
        assert len(thoughts) == 3
        assert thoughts == ["Step 1", "Step 2", "Step 3"]
        
        # Verify process interaction
        process_mock.stdin.write.assert_called_once()
        process_mock.stdin.drain.assert_called_once()
        process_mock.stdout.readline.assert_called_once()

@pytest.mark.skip_mcp
@pytest.mark.asyncio
async def test_process_thought_server_error(mcp_server):
    # Mock process with error
    process_mock = AsyncMock()
    process_mock.stdin = AsyncMock()
    process_mock.stdout = AsyncMock()
    process_mock.stdout.readline.return_value = b''  # Empty response
    
    # Mock process creation
    with patch('asyncio.create_subprocess_exec', return_value=process_mock):
        # Test error handling
        with pytest.raises(Exception, match="No response from server"):
            await mcp_server.process_thought(
                context="Test context",
                query="What are the steps?"
            )
            
@pytest.mark.skip_mcp
@pytest.mark.asyncio
async def test_server_lifecycle(mcp_server):
    # Mock process
    process_mock = AsyncMock()
    process_mock.stdin = AsyncMock()
    process_mock.stdout = AsyncMock()
    
    # Mock process creation
    with patch('asyncio.create_subprocess_exec', return_value=process_mock):
        # Start server
        await mcp_server.start()
        assert mcp_server.process is not None
        
        # Stop server
        await mcp_server.stop()
        assert mcp_server.process is None
        process_mock.terminate.assert_called_once()
