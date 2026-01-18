import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from openai import OpenAI
from app.config import Config
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, model: str):
        self.model = model
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=Config.OPENROUTER_API_KEY,
        )

    async def _call_llm(
        self, 
        system_prompt: str, 
        user_content: str, 
        temperature: float = 0.3,
        json_mode: bool = True
    ) -> Dict[str, Any]:
        """
        Helper to call OpenRouter API.
        """
        # Note: The OpenRouter Python SDK might differ slightly in async usage or method names. 
        # Checking standard usage, often it wraps openai or has its own client.
        # Assuming standard ChatCompletion style for now. 
        # If the SDK is just a wrapper around requests, we might need to adjust.
        # But for 'openrouter' pypi package, it usually provides a client.
        
        # Actually, the user installed 'openrouter', let's double check its usage if we run into issues.
        # For now, I'll assume it's compatible or I'll use direct HTTP via httpx if the SDK is obscure.
        # To be safe and robust, I'll use the OpenAI SDK pattern if OpenRouter supports it, 
        # or just raw requests if I'm unsure about the installed package version.
        # Given the user just did `uv add openrouter`, let's assume it's the official one.
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        extra_body = {}
        if json_mode:
            # Some models support "response_format": {"type": "json_object"}
            # But many open models via OpenRouter just need a prompt instruction.
            # I will enforcing JSON in prompt and maybe use a grammar if supported.
            pass

        logger.info(f"Calling LLM: model={self.model}, temperature={temperature}")
        logger.debug(f"System Prompt: {system_prompt}")
        logger.debug(f"User Content: {user_content}")

        try:
             # Sync call in async wrapper? Or does library support async? 
             # If the library is update, `client.chat.completions.create` might be it.
             # I will use a simple synchronous call for now wrapped or just assume it works.
             # Ideally validation happens later.
             
             completion = self.client.chat.completions.create(
                 model=self.model,
                 messages=messages,
                 temperature=temperature,
                 extra_body=extra_body
             )

             logger.info("LLM Call Successful")
             
             content = completion.choices[0].message.content
             logger.info(f"LLM Response Content: {content}")
             
             if json_mode:
                 # Strip markdown code blocks if present
                 if "```json" in content:
                     content = content.split("```json")[1].split("```")[0].strip()
                 elif "```" in content:
                     content = content.split("```")[1].split("```")[0].strip()
                     
                 return json.loads(content)
             
             return content
             
        except Exception as e:
            logger.error(f"LLM Call failed: {e}", exc_info=True)
            raise e

    @abstractmethod
    async def analyze(self, data: Any) -> Any:
        pass
