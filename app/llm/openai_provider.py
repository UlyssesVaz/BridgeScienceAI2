# app/llm/openai_provider.py

import os
import json
import logging
from typing import Optional, Dict, Any
import asyncio

from app.llm.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI LLM provider implementation.
    Handles API calls, retries, and error handling for OpenAI's API.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY env var not set")
        
        self.model = model
        
        # Import OpenAI client (lazy import to avoid import errors if not installed)
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion from OpenAI.
        
        Implements retry logic with exponential backoff (3 attempts).
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Retry configuration
        max_retries = 3
        base_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"OpenAI API call attempt {attempt + 1}/{max_retries}",
                    extra={
                        "model": self.model,
                        "max_tokens": max_tokens,
                        "temperature": temperature
                    }
                )
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
                
                content = response.choices[0].message.content
                
                # Extract metadata
                metadata = {
                    "model": response.model,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    "finish_reason": response.choices[0].finish_reason
                }
                
                logger.info(
                    "OpenAI API call successful",
                    extra={
                        "model": self.model,
                        "tokens_used": metadata["usage"]["total_tokens"]
                    }
                )
                
                return LLMResponse(content=content, metadata=metadata)
                
            except Exception as e:
                logger.warning(
                    f"OpenAI API call failed (attempt {attempt + 1}/{max_retries})",
                    extra={"error": str(e), "attempt": attempt + 1}
                )
                
                if attempt == max_retries - 1:
                    # Last attempt failed - give up
                    logger.error(
                        "OpenAI API call failed after all retries",
                        extra={"error": str(e)},
                        exc_info=True
                    )
                    raise
                
                # Exponential backoff
                delay = base_delay * (2 ** attempt)
                logger.debug(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
        
        # Should never reach here, but just in case
        raise RuntimeError("Failed to generate response after retries")