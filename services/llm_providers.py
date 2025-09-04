import os
import json
import requests
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
        self.base_url = "https://api.deepseek.com/v1"

    def generate(self, prompt: str) -> LLMResult:
        if not self.api_key:
            return LLMResult(
                content="Error: DeepSeek API key no configurada. Por favor verifica tu archivo .env",
                raw={"error": "missing_api_key"}
            )
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return LLMResult(content=content, raw=result)
            else:
                return LLMResult(
                    content=f"Error API DeepSeek: {response.status_code} - {response.text}",
                    raw={"error": response.text, "status_code": response.status_code}
                )
                
        except requests.exceptions.RequestException as e:
            return LLMResult(
                content=f"Error de conexión con DeepSeek: {str(e)}",
                raw={"error": str(e)}
            )
        except Exception as e:
            return LLMResult(
                content=f"Error inesperado: {str(e)}",
                raw={"error": str(e)}
            )

class SonnetClient:
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229", temperature: float = 0.1, max_tokens: int = 2000):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = "https://api.anthropic.com/v1"

    def generate_json(self, prompt: str, schema: dict) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "error": "Sonnet API key no configurada. Por favor verifica tu archivo .env",
                "currency": "USD",
                "items": [],
                "summary_by_category": {},
                "total": 0.0,
                "assumptions": [],
                "compliance_notes": []
            }
        
        try:
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            system_prompt = f"""Debes generar una respuesta en formato JSON que siga exactamente este esquema:
{json.dumps(schema, indent=2)}

Asegúrate de que la respuesta sea un JSON válido y completo."""
            
            data = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "system": system_prompt,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["content"][0]["text"]
                
                # Try to parse JSON from the response
                try:
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    json_content = content[json_start:json_end]
                    return json.loads(json_content)
                except (json.JSONDecodeError, ValueError):
                    return {
                        "error": f"No se pudo parsear JSON de la respuesta: {content}",
                        "currency": "USD",
                        "items": [],
                        "summary_by_category": {},
                        "total": 0.0,
                        "assumptions": [],
                        "compliance_notes": []
                    }
            else:
                return {
                    "error": f"Error API Sonnet: {response.status_code} - {response.text}",
                    "currency": "USD",
                    "items": [],
                    "summary_by_category": {},
                    "total": 0.0,
                    "assumptions": [],
                    "compliance_notes": []
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Error de conexión con Sonnet: {str(e)}",
                "currency": "USD",
                "items": [],
                "summary_by_category": {},
                "total": 0.0,
                "assumptions": [],
                "compliance_notes": []
            }
        except Exception as e:
            return {
                "error": f"Error inesperado: {str(e)}",
                "currency": "USD",
                "items": [],
                "summary_by_category": {},
                "total": 0.0,
                "assumptions": [],
                "compliance_notes": []
            }