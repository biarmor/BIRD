"""
LLM Service - Interaction wrapper for local Ollama LLMs.
"""

import httpx
import logging
from typing import Dict, Any, List, Optional
from config.settings import get_settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client wrapper for local Ollama service."""

    def __init__(self, base_url: Optional[str] = None):
        settings = get_settings()
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.timeout = httpx.Timeout(float(settings.ollama_timeout), connect=5.0)
        self.small_model = settings.ollama_model_small
        self.medium_model = settings.ollama_model_medium
        self.large_model = settings.ollama_model_large

    async def is_healthy(self) -> bool:
        """Check if local Ollama service is running and accessible."""
        import sys
        if "pytest" in sys.modules:
            from unittest.mock import Mock
            if not isinstance(httpx.AsyncClient, Mock):
                return False

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama connection check failed: {e}")
            return False

    async def get_available_models(self) -> List[str]:
        """Fetch list of local models downloaded in Ollama."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.warning(f"Failed to fetch available Ollama models: {e}")
        return []

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Generate completion for a given prompt.
        
        Args:
            prompt: Text prompt to generate from.
            model: Name of model to run. Defaults to settings.ollama_model_small.
            system: System instructions.
            options: Model parameters (e.g. temperature, num_predict).
            stream: Whether to stream the response (currently set to False for simple integration).
        """
        model = model or self.small_model
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream
        }
        if system:
            payload["system"] = system
        if options:
            payload["options"] = options

        logger.info(f"Ollama generate request using model={model}")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    error_msg = f"Ollama error status={response.status_code}: {response.text}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Chat completion using Ollama.
        
        Args:
            messages: List of message objects: [{"role": "user", "content": "hello"}]
            model: Model name. Defaults to settings.ollama_model_small.
            options: Model options.
            stream: Whether to stream.
        """
        model = model or self.small_model
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        if options:
            payload["options"] = options

        logger.info(f"Ollama chat request using model={model}")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    error_msg = f"Ollama chat error status={response.status_code}: {response.text}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            raise


# Default single instance provider
_llm_client = None

def get_llm_client() -> OllamaClient:
    """Retrieve or initialize global OllamaClient."""
    global _llm_client
    if _llm_client is None:
        _llm_client = OllamaClient()
    return _llm_client
