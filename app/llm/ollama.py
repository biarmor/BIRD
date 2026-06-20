import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    def get_model_name(self) -> str:
        return "qwen3:14b"

    def generate(self, prompt: str, model: str = "qwen3:14b") -> str:
        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120.0
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                raise RuntimeError(f"Ollama error: {response.text}")
        except Exception as e:
            logger.error(f"Ollama generate failed: {e}")
            raise e
