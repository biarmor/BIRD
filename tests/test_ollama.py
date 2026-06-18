"""
Tests for Ollama Client and agent integrations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.llm_service import OllamaClient, get_llm_client
from app.agents.forge_agent import ForgeAgent, AssetType, ContentTone
from app.agents.reasoning_agent import ReasoningAgent


@pytest.fixture
def mock_httpx_client():
    with patch("httpx.AsyncClient") as mock:
        yield mock


@pytest.mark.asyncio
async def test_ollama_client_healthy(mock_httpx_client):
    """Test is_healthy returns True on status 200."""
    client_instance = mock_httpx_client.return_value.__aenter__.return_value
    client_instance.get = AsyncMock(return_value=MagicMock(status_code=200))
    
    ollama_client = OllamaClient(base_url="http://localhost:11434")
    assert await ollama_client.is_healthy() is True


@pytest.mark.asyncio
async def test_ollama_client_unhealthy(mock_httpx_client):
    """Test is_healthy returns False on exception or connection error."""
    client_instance = mock_httpx_client.return_value.__aenter__.return_value
    client_instance.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
    
    ollama_client = OllamaClient(base_url="http://localhost:11434")
    assert await ollama_client.is_healthy() is False


@pytest.mark.asyncio
async def test_ollama_client_get_available_models(mock_httpx_client):
    """Test retrieving available models from Ollama."""
    client_instance = mock_httpx_client.return_value.__aenter__.return_value
    mock_response = MagicMock(status_code=200)
    mock_response.json.return_value = {
        "models": [
            {"name": "qwen2.5:7b"},
            {"name": "mistral:7b"}
        ]
    }
    client_instance.get = AsyncMock(return_value=mock_response)
    
    ollama_client = OllamaClient()
    models = await ollama_client.get_available_models()
    assert models == ["qwen2.5:7b", "mistral:7b"]


@pytest.mark.asyncio
async def test_ollama_client_generate_success(mock_httpx_client):
    """Test successful prompt generation."""
    client_instance = mock_httpx_client.return_value.__aenter__.return_value
    mock_response = MagicMock(status_code=200)
    mock_response.json.return_value = {
        "model": "qwen2.5:7b",
        "created_at": "2026-06-18T07:00:00Z",
        "response": "Hello world response",
        "done": True
    }
    client_instance.post = AsyncMock(return_value=mock_response)
    
    ollama_client = OllamaClient()
    res = await ollama_client.generate(prompt="Hello", model="qwen2.5:7b")
    assert res["response"] == "Hello world response"


@pytest.mark.asyncio
async def test_ollama_client_chat_success(mock_httpx_client):
    """Test successful chat message completion."""
    client_instance = mock_httpx_client.return_value.__aenter__.return_value
    mock_response = MagicMock(status_code=200)
    mock_response.json.return_value = {
        "model": "qwen2.5:7b",
        "message": {
            "role": "assistant",
            "content": "Hi there!"
        },
        "done": True
    }
    client_instance.post = AsyncMock(return_value=mock_response)
    
    ollama_client = OllamaClient()
    res = await ollama_client.chat(messages=[{"role": "user", "content": "Hi"}])
    assert res["message"]["content"] == "Hi there!"


@pytest.mark.asyncio
async def test_forge_agent_llm_integration():
    """Test ForgeAgent calls LLM and falls back on failure."""
    mock_ollama = MagicMock(spec=OllamaClient)
    mock_ollama.is_healthy = AsyncMock(return_value=True)
    mock_ollama.generate = AsyncMock(return_value={"response": "LLM Generated Social Post"})

    agent = ForgeAgent(llm_client=mock_ollama)
    
    # 1. Test success generation
    asset = await agent.generate_asset(
        asset_type=AssetType.SOCIAL_POST,
        context={"topic": "AI news", "hashtags": ["#ai"]},
        tone=ContentTone.PROFESSIONAL
    )
    assert asset.content == "LLM Generated Social Post"
    mock_ollama.generate.assert_called_once()
    
    # 2. Test fallback when healthy check fails or exception is raised
    mock_ollama.generate.reset_mock()
    mock_ollama.is_healthy = AsyncMock(return_value=False)
    
    asset_fallback = await agent.generate_asset(
        asset_type=AssetType.SOCIAL_POST,
        context={"topic": "AI news", "hashtags": ["#ai"]},
        tone=ContentTone.PROFESSIONAL
    )
    assert "Check out this: AI news" in asset_fallback.content
    mock_ollama.generate.assert_not_called()


@pytest.mark.asyncio
async def test_reasoning_agent_llm_integration():
    """Test ReasoningAgent calls LLM for causality analysis and falls back on failure."""
    mock_ollama = MagicMock(spec=OllamaClient)
    mock_ollama.is_healthy = AsyncMock(return_value=True)
    mock_ollama.generate = AsyncMock(return_value={
        "response": "Cause A\nCause B\n- Cause C"
    })

    agent = ReasoningAgent(llm_client=mock_ollama)
    
    # 1. Test success generation
    result = await agent.analyze_causality(
        effect="Drop in product sales",
        context={"industry": "retail"}
    )
    assert "Cause A" in result["potential_causes"]
    assert "Cause B" in result["potential_causes"]
    assert "Cause C" in result["potential_causes"]
    mock_ollama.generate.assert_called_once()
    
    # 2. Test fallback on error
    mock_ollama.generate.reset_mock()
    mock_ollama.is_healthy = AsyncMock(side_effect=RuntimeError("Ollama offline"))
    
    result_fallback = await agent.analyze_causality(
        effect="Drop in product sales",
        context={"industry": "retail"}
    )
    assert "Market competition" in result_fallback["potential_causes"]
    mock_ollama.generate.assert_not_called()


def test_get_llm_client_singleton():
    """Test that get_llm_client returns a singleton instance."""
    c1 = get_llm_client()
    c2 = get_llm_client()
    assert c1 is c2
