# services/llm_providers.py
import os
import re
import json
import requests
from dataclasses import dataclass
from typing import Any, Dict, Optional, List


# ---------- Shared result type ----------
@dataclass
class LLMResult:
    content: str
    raw: Dict[str, Any]


# ---------- DeepSeek (narrative) ----------
class DeepSeekClient:
    def __init__(
        self,
        api_key: Optional[str],
        model: str = "deepseek-chat",
        temperature: float = 0.2,
        max_tokens: int = 4000,
        base_url: str = "https://api.deepseek.com/v1",
        timeout_s: int = 300,
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def generate(self, prompt: str) -> LLMResult:
        if not self.api_key:
            return LLMResult(
                content="Error: DeepSeek API key no configurada. Por favor verifica tu archivo .env",
                raw={"error": "missing_api_key"},
            )

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=self.timeout_s,
            )

            if resp.status_code == 200:
                result = resp.json()
                content = result["choices"][0]["message"]["content"]
                return LLMResult(content=content, raw=result)

            return LLMResult(
                content=f"Error API DeepSeek: {resp.status_code} - {resp.text}",
                raw={"error": resp.text, "status_code": resp.status_code},
            )

        except requests.exceptions.Timeout:
            return LLMResult(
                content=(
                    "Error: DeepSeek API timeout. El documento es muy grande o la respuesta "
                    "está tardando demasiado. Intenta con un documento más pequeño."
                ),
                raw={"error": "timeout"},
            )
        except requests.exceptions.RequestException as e:
            return LLMResult(
                content=f"Error de conexión con DeepSeek: {str(e)}", raw={"error": str(e)}
            )
        except Exception as e:
            return LLMResult(
                content=f"Error inesperado: {str(e)}", raw={"error": str(e)}
            )


# ---------- Sonnet / Anthropic (budget) ----------
class SonnetClient:
    """
    Calls Anthropic Messages API and guarantees we return a dict.
    Adds robust JSON extraction to handle ```json fences or extra prose.
    """

    def __init__(
        self,
        api_key: Optional[str],
        model: str = "claude-sonnet-4-20250514",  # solid current model id
        temperature: float = 0.0,  # deterministic budgets
        max_tokens: int = 16000,
        base_url: str = "https://api.anthropic.com/v1",
        timeout_s: int = 180,
    ):
        self.api_key = api_key or os.getenv("SONNET_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    # ---------- helpers ----------
    @staticmethod
    def _strip_code_fences(text: str) -> str:
        """
        Remove leading ```json/``` fences and trailing ``` (case-insensitive) with optional whitespace.
        """
        text = re.sub(r"^\s*```(?:json)?\s*\n", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\n\s*```\s*$", "", text)
        return text.strip()

    @staticmethod
    def _extract_first_json(text: str) -> str:
        """
        Return the first balanced JSON object/array in text.
        Tries quick parse first, then scans for balanced braces/brackets.
        """
        text = text.strip()
        # quick path
        try:
            json.loads(text)
            return text
        except Exception:
            pass

        starts: List[int] = [i for i, ch in enumerate(text) if ch in "{["]
        for start in starts:
            stack: List[str] = []
            in_str = False
            esc = False
            for i in range(start, len(text)):
                ch = text[i]
                if in_str:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == '"':
                        in_str = False
                else:
                    if ch == '"':
                        in_str = True
                    elif ch in "{[":
                        stack.append(ch)
                    elif ch in "}]":
                        if not stack:
                            break
                        opener = stack.pop()
                        if (opener, ch) not in {("{", "}"), ("[", "]")}:
                            break
                        if not stack:
                            candidate = text[start : i + 1]
                            try:
                                json.loads(candidate)
                                return candidate
                            except Exception:
                                break
        raise ValueError("No valid JSON found")

    # ---------- public ----------
    def generate_json(self, prompt: str, schema: dict) -> Dict[str, Any]:
        empty = {
            "currency": "USD",
            "items": [],
            "summary_by_category": {},
            "total": 0.0,
            "assumptions": [],
            "compliance_notes": [],
        }

        if not self.api_key:
            return {
                **empty,
                "error": "Sonnet API key no configurada. Define SONNET_API_KEY o ANTHROPIC_API_KEY en .env.",
            }

        try:
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            }

            system_prompt = (
                "Eres un oficial financiero de donantes. Devuelve SOLO JSON válido que cumpla el esquema. "
                "No incluyas bloques de código ni texto adicional. Si no estás seguro, devuelve un JSON "
                "válido con estructuras vacías."
            )

            user_prompt = (
                "ESQUEMA_JSON:\n"
                + json.dumps(schema)
                + "\n\nTAREA:\n"
                + prompt
                + "\n\nDEVUELVE SOLO JSON. SIN ```."
            )

            data = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            }

            resp = requests.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=data,
                timeout=self.timeout_s,
            )

            if resp.status_code != 200:
                msg = resp.text
                if resp.status_code == 404:
                    msg += (
                        f"\n\nModelo utilizado: {self.model}\n"
                        "Sugeridos: claude-3-5-sonnet-20241022, claude-3-5-sonnet-20240620"
                    )
                return {**empty, "error": f"Error API Sonnet: {resp.status_code} - {msg}"}

            result = resp.json()
            # Messages API returns a list of content blocks; take text blocks
            content_blocks = result.get("content", [])
            text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text").strip()

            # 1) strip fences; 2) extract balanced JSON
            cleaned = self._strip_code_fences(text)
            try:
                json_str = self._extract_first_json(cleaned)
                return json.loads(json_str)
            except Exception:
                # Last resort: show raw so caller can inspect
                return {**empty, "error": f"No se pudo parsear JSON de la respuesta: {text}"}

        except requests.exceptions.Timeout:
            return {**empty, "error": "Sonnet API timeout. La generación del presupuesto tardó demasiado."}
        except requests.exceptions.RequestException as e:
            return {**empty, "error": f"Error de conexión con Sonnet: {str(e)}"}
        except Exception as e:
            return {**empty, "error": f"Error inesperado: {str(e)}"}

    def test_connection(self) -> bool:
        """Ping small completion to validate API key/model."""
        if not self.api_key:
            return False
        try:
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            }
            data = {
                "model": self.model,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Test"}],
            }
            resp = requests.post(f"{self.base_url}/messages", headers=headers, json=data, timeout=30)
            return resp.status_code == 200
        except Exception:
            return False


# ---------- Convenience helpers ----------
def get_available_models() -> Dict[str, list]:
    """Current model names you might want to probe."""
    return {
        "deepseek": ["deepseek-chat"],
        "sonnet": [
            "claude-3-5-sonnet-20241022",  # current stable
            "claude-3-5-sonnet-20240620",  # previous
            "claude-sonnet-4-20250514",    # future/alt id (if enabled in your account)
        ],
    }


def create_test_clients() -> Dict[str, Dict[str, Any]]:
    """
    Quick smoke test for keys and a working Anthropic model.
    Returns:
      {
        "deepseek": {"available": bool, "error": str|None},
        "sonnet": {"available": bool, "error": str|None, "working_model": str|None}
      }
    """
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    sonnet_key = os.getenv("SONNET_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

    results = {
        "deepseek": {"available": False, "error": None},
        "sonnet": {"available": False, "error": None, "working_model": None},
    }

    # DeepSeek test
    if deepseek_key:
        try:
            ds = DeepSeekClient(deepseek_key)
            r = ds.generate("Test")
            results["deepseek"]["available"] = not r.content.startswith("Error")
            if not results["deepseek"]["available"]:
                results["deepseek"]["error"] = r.content
        except Exception as e:
            results["deepseek"]["error"] = str(e)
    else:
        results["deepseek"]["error"] = "DEEPSEEK_API_KEY no encontrado"

    # Sonnet test
    if sonnet_key:
        for model in get_available_models()["sonnet"]:
            try:
                sc = SonnetClient(sonnet_key, model=model)
                if sc.test_connection():
                    results["sonnet"]["available"] = True
                    results["sonnet"]["working_model"] = model
                    break
            except Exception:
                continue
        if not results["sonnet"]["available"]:
            results["sonnet"]["error"] = "Ninguno de los modelos respondió correctamente"
    else:
        results["sonnet"]["error"] = "SONNET_API_KEY o ANTHROPIC_API_KEY no encontrado"

    return results
