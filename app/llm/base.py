# app/llm/base.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pydantic import BaseModel


class LLMResponse(BaseModel):
    """
    Standard wrapper for all LLM responses.
    Ensures consistent structure across different providers.
    """
    content: str  # The actual response text
    metadata: Dict[str, Any] = {}  # Provider-specific metadata (tokens used, model, etc.)


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.

    Why: This interface ensures we can swap OpenAI for Anthropic (or any other provider)
    without changing agent code. The agent only knows "give me a response" - it doesn't
    care whether it's GPT-4 or Claude.

    Contract:
    - All providers must implement async generate()
    - All providers return LLMResponse
    - All providers handle their own retry logic
    - All providers handle their own API key management
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a completion from the LLM.

        Args:
            prompt: The user/agent prompt (the question or request)
            system_prompt: Optional system instructions (sets behavior/role)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            **kwargs: Provider-specific parameters (e.g., top_p, frequency_penalty)

        Returns:
            LLMResponse containing the generated text and metadata

        Raises:
            Exception: If generation fails after retries
        """
        raise NotImplementedError("Subclass must implement generate()")
