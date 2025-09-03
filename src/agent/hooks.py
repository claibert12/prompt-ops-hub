"""LLM integration hooks for ChatGPT/Claude."""

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

from openai import OpenAI

logger = logging.getLogger(__name__)


@dataclass
class LLMRequest:
    """Request to LLM service."""
    prompt: str
    model: str = "gpt-4"
    temperature: float = 0.1
    max_tokens: int = 4000
    system_message: Optional[str] = None


@dataclass
class LLMResponse:
    """Response from LLM service."""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str


class LLMHooks:
    """Hooks for LLM service integration."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or "stub_key"
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.client: OpenAI | None = None
        if self.api_key != "stub_key":
            try:
                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to init OpenAI client: %s", exc)
                self.client = None

    async def send_request(self, request: LLMRequest) -> LLMResponse:
        """Send request to LLM service.

        Uses real OpenAI API when credentials are available; otherwise
        returns a stubbed response for testing.
        """
        logger.info("Sending request to %s", request.model)

        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=request.model,
                    messages=[
                        {"role": "system", "content": request.system_message or ""},
                        {"role": "user", "content": request.prompt},
                    ],
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                )
                message = response.choices[0].message.content
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                finish_reason = response.choices[0].finish_reason or "stop"
                return LLMResponse(
                    content=message,
                    model=request.model,
                    usage=usage,
                    finish_reason=finish_reason,
                )
            except Exception as exc:  # pragma: no cover - network/credentials
                logger.warning("LLM request failed: %s", exc)

        await asyncio.sleep(0.1)
        stub_content = (
            f"# Stub response for: {request.prompt[:50]}...\n\n"
            "This is a placeholder response. Implement actual LLM API integration here."
        )
        return LLMResponse(
            content=stub_content,
            model=request.model,
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            finish_reason="stop",
        )
    
    async def send_chat_request(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Send chat-style request to LLM service."""
        # Convert messages to prompt format
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        
        request = LLMRequest(
            prompt=prompt,
            **kwargs
        )
        
        return await self.send_request(request)
    
    async def send_code_generation_request(self, task_description: str, context: str = "") -> LLMResponse:
        """Send code generation request."""
        prompt = f"""Task: {task_description}

Context: {context}

Please generate the code changes needed to complete this task. Include:
1. File modifications with unified diff format
2. Any new files needed
3. Test updates if required

Response:"""
        
        request = LLMRequest(
            prompt=prompt,
            model="gpt-4",
            temperature=0.1,
            max_tokens=6000
        )
        
        return await self.send_request(request)
    
    async def send_test_generation_request(self, code_changes: str, task_description: str) -> LLMResponse:
        """Send test generation request."""
        prompt = f"""Code Changes: {code_changes}

Task: {task_description}

Please generate comprehensive tests for the above code changes. Include:
1. Unit tests for new functionality
2. Integration tests if needed
3. Edge case coverage

Response:"""
        
        request = LLMRequest(
            prompt=prompt,
            model="gpt-4",
            temperature=0.1,
            max_tokens=4000
        )
        
        return await self.send_request(request)


# Global instance
llm_hooks = LLMHooks()


async def send_to_chatgpt(prompt: str, **kwargs) -> str:
    """Send prompt to ChatGPT and return response."""
    request = LLMRequest(prompt=prompt, **kwargs)
    response = await llm_hooks.send_request(request)
    return response.content


async def send_to_claude(prompt: str, **kwargs) -> str:
    """Send prompt to Claude and return response."""
    # TODO: Implement Claude API integration
    request = LLMRequest(prompt=prompt, model="claude-3-sonnet", **kwargs)
    response = await llm_hooks.send_request(request)
    return response.content


async def generate_code(task_description: str, context: str = "") -> str:
    """Generate code for a task."""
    response = await llm_hooks.send_code_generation_request(task_description, context)
    return response.content


async def generate_tests(code_changes: str, task_description: str) -> str:
    """Generate tests for code changes."""
    response = await llm_hooks.send_test_generation_request(code_changes, task_description)
    return response.content 