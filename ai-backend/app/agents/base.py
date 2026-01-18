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
