"""LLM provider integrations for content description."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import base64
import os
import logging
from dataclasses import dataclass

logger = logging.getLogger("arxiv-mcp-server.llm-providers")


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None


class LLMProvider(ABC):
    """Base class for LLM providers."""
    
    @abstractmethod
    async def describe_image(self, image_base64: str, prompt: str) -> LLMResponse:
        """Describe an image using the LLM."""
        pass
    
    @abstractmethod
    async def describe_text(self, text: str, prompt: str) -> LLMResponse:
        """Describe text content using the LLM."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT-4 Vision provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-vision-preview"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"
        
    async def describe_image(self, image_base64: str, prompt: str) -> LLMResponse:
        """Describe an image using GPT-4 Vision."""
        try:
            import httpx
            
            if not self.api_key:
                return LLMResponse(
                    content="",
                    model=self.model,
                    error="OpenAI API key not provided"
                )
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 500
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url, json=data, headers=headers)
                response.raise_for_status()
                result = response.json()
            
            return LLMResponse(
                content=result["choices"][0]["message"]["content"],
                model=self.model,
                usage=result.get("usage")
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return LLMResponse(
                content="",
                model=self.model,
                error=str(e)
            )
    
    async def describe_text(self, text: str, prompt: str) -> LLMResponse:
        """Describe text content using GPT-4."""
        try:
            import httpx
            
            if not self.api_key:
                return LLMResponse(
                    content="",
                    model=self.model,
                    error="OpenAI API key not provided"
                )
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4-turbo-preview",  # Use text model for tables
                "messages": [
                    {
                        "role": "user",
                        "content": f"{prompt}\n\n{text}"
                    }
                ],
                "max_tokens": 500
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url, json=data, headers=headers)
                response.raise_for_status()
                result = response.json()
            
            return LLMResponse(
                content=result["choices"][0]["message"]["content"],
                model="gpt-4-turbo-preview",
                usage=result.get("usage")
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return LLMResponse(
                content="",
                model="gpt-4-turbo-preview",
                error=str(e)
            )


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.base_url = "https://api.anthropic.com/v1/messages"
        
    async def describe_image(self, image_base64: str, prompt: str) -> LLMResponse:
        """Describe an image using Claude."""
        try:
            import httpx
            
            if not self.api_key:
                return LLMResponse(
                    content="",
                    model=self.model,
                    error="Anthropic API key not provided"
                )
            
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_base64
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 500
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url, json=data, headers=headers)
                response.raise_for_status()
                result = response.json()
            
            return LLMResponse(
                content=result["content"][0]["text"],
                model=self.model,
                usage=result.get("usage")
            )
            
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            return LLMResponse(
                content="",
                model=self.model,
                error=str(e)
            )
    
    async def describe_text(self, text: str, prompt: str) -> LLMResponse:
        """Describe text content using Claude."""
        try:
            import httpx
            
            if not self.api_key:
                return LLMResponse(
                    content="",
                    model=self.model,
                    error="Anthropic API key not provided"
                )
            
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": f"{prompt}\n\n{text}"
                    }
                ],
                "max_tokens": 500
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url, json=data, headers=headers)
                response.raise_for_status()
                result = response.json()
            
            return LLMResponse(
                content=result["content"][0]["text"],
                model=self.model,
                usage=result.get("usage")
            )
            
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            return LLMResponse(
                content="",
                model=self.model,
                error=str(e)
            )


class MockProvider(LLMProvider):
    """Mock provider for testing without API calls."""
    
    async def describe_image(self, image_base64: str, prompt: str) -> LLMResponse:
        """Mock image description."""
        return LLMResponse(
            content=(
                "This appears to be a figure from an academic paper. "
                "[Mock description - in production this would be an actual LLM analysis]"
            ),
            model="mock",
            usage={"prompt_tokens": 100, "completion_tokens": 50}
        )
    
    async def describe_text(self, text: str, prompt: str) -> LLMResponse:
        """Mock text description."""
        # Simple analysis of table structure
        lines = text.strip().split('\n')
        return LLMResponse(
            content=(
                f"This appears to be a data table with approximately {len(lines)} rows. "
                "[Mock description - in production this would be an actual LLM analysis]"
            ),
            model="mock",
            usage={"prompt_tokens": 100, "completion_tokens": 50}
        )


def get_llm_provider(provider_name: str = "mock", **kwargs) -> LLMProvider:
    """Factory function to get an LLM provider instance."""
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "mock": MockProvider,
    }
    
    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        logger.warning(f"Unknown provider {provider_name}, using mock provider")
        return MockProvider()
    
    return provider_class(**kwargs)