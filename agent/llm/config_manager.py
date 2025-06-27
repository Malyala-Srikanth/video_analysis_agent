import os
from typing import Any, Dict

class AgentsLLMConfigManager:
    _instance = None
    _config = None

    def __init__(self):
        if AgentsLLMConfigManager._instance is not None:
            raise RuntimeError("Use get_instance() instead")
        AgentsLLMConfigManager._instance = self
        self._config = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_agent_config(self) -> Dict[str, Any]:
        # Hardcoded config for standalone use
        # You can edit this as needed for your environment
        return {
            "model_config_params": {
                "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            },
            "llm_config_params": {
                "cache_seed": 12345,
                "temperature": 0.0,
                "seed": 12345
            }
        } 