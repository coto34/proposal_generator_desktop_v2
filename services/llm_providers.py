from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class LLMResult:
    content: str
    raw: Dict[str, Any]

class DeepSeekClient:
    def __init__(self, api_key: str, model: str = "deepseek-chat", temperature: float = 0.2, max_tokens: int = 4000):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(self, prompt: str) -> LLMResult:
        return LLMResult(content="Demo DeepSeek output", raw={"ok": True})

class SonnetClient:
    def __init__(self, api_key: str, model: str = "sonnet-3", temperature: float = 0.1, max_tokens: int = 2000):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate_json(self, prompt: str, schema: dict) -> Dict[str, Any]:
        return {"currency":"USD","items":[],"summary_by_category":{},"total":0.0,"assumptions":[],"compliance_notes":[]}
