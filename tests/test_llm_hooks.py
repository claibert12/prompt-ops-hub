"""Unit tests for LLM hooks."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.agent.hooks import (
    LLMHooks, LLMRequest, LLMResponse,
    send_to_chatgpt, send_to_claude,
    generate_code, generate_tests
)


class TestLLMHooks:
    """Test cases for LLMHooks class."""

    def test_llm_request_initialization(self):
        """Test LLMRequest initialization."""
        request = LLMRequest(
            prompt="Test prompt",
            model="gpt-4",
            temperature=0.5,
            max_tokens=2000
        )
        assert request.prompt == "Test prompt"
        assert request.model == "gpt-4"
        assert request.temperature == 0.5
        assert request.max_tokens == 2000
        assert request.system_message is None

    def test_llm_response_initialization(self):
        """Test LLMResponse initialization."""
        response = LLMResponse(
            content="Test response",
            model="gpt-4",
            usage={"prompt_tokens": 100, "completion_tokens": 50},
            finish_reason="stop"
        )
        assert response.content == "Test response"
        assert response.model == "gpt-4"
        assert response.usage == {"prompt_tokens": 100, "completion_tokens": 50}
        assert response.finish_reason == "stop"

    def test_llm_hooks_initialization(self):
        """Test LLMHooks initialization."""
        hooks = LLMHooks(api_key="test_key")
        assert hooks.api_key == "test_key"
        assert hooks.base_url == "https://api.openai.com/v1"

    def test_llm_hooks_default_initialization(self):
        """Test LLMHooks initialization with default values."""
        hooks = LLMHooks()
        assert hooks.api_key == "stub_key"
        assert hooks.base_url == "https://api.openai.com/v1"

    @pytest.mark.asyncio
    async def test_send_request_stub_response(self):
        """Test send_request returns stub response."""
        hooks = LLMHooks()
        request = LLMRequest(prompt="Test prompt")
        
        response = await hooks.send_request(request)
        
        assert isinstance(response, LLMResponse)
        assert "Test prompt" in response.content
        assert response.model == "gpt-4"
        assert response.usage["total_tokens"] == 150
        assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_send_chat_request(self):
        """Test send_chat_request converts messages to prompt."""
        hooks = LLMHooks()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        
        with patch.object(hooks, 'send_request') as mock_send:
            mock_response = LLMResponse(
                content="Test response",
                model="gpt-4",
                usage={"total_tokens": 100},
                finish_reason="stop"
            )
            mock_send.return_value = mock_response
            
            response = await hooks.send_chat_request(messages)
            
            # Verify send_request was called with converted prompt
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            assert "user: Hello" in call_args.prompt
            assert "assistant: Hi there" in call_args.prompt

    @pytest.mark.asyncio
    async def test_send_code_generation_request(self):
        """Test send_code_generation_request creates proper prompt."""
        hooks = LLMHooks()
        task_description = "Add a new API endpoint"
        context = "FastAPI application"
        
        with patch.object(hooks, 'send_request') as mock_send:
            mock_response = LLMResponse(
                content="Generated code",
                model="gpt-4",
                usage={"total_tokens": 100},
                finish_reason="stop"
            )
            mock_send.return_value = mock_response
            
            response = await hooks.send_code_generation_request(task_description, context)
            
            # Verify send_request was called with code generation prompt
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            assert task_description in call_args.prompt
            assert context in call_args.prompt
            assert "unified diff format" in call_args.prompt
            assert call_args.model == "gpt-4"
            assert call_args.max_tokens == 6000

    @pytest.mark.asyncio
    async def test_send_test_generation_request(self):
        """Test send_test_generation_request creates proper prompt."""
        hooks = LLMHooks()
        code_changes = "def new_function(): pass"
        task_description = "Add unit tests"
        
        with patch.object(hooks, 'send_request') as mock_send:
            mock_response = LLMResponse(
                content="Generated tests",
                model="gpt-4",
                usage={"total_tokens": 100},
                finish_reason="stop"
            )
            mock_send.return_value = mock_response
            
            response = await hooks.send_test_generation_request(code_changes, task_description)
            
            # Verify send_request was called with test generation prompt
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            assert code_changes in call_args.prompt
            assert task_description in call_args.prompt
            assert "Unit tests" in call_args.prompt
            assert call_args.model == "gpt-4"
            assert call_args.max_tokens == 4000


class TestLLMFunctions:
    """Test cases for LLM utility functions."""

    @pytest.mark.asyncio
    async def test_send_to_chatgpt(self):
        """Test send_to_chatgpt function."""
        with patch('src.agent.hooks.llm_hooks') as mock_hooks:
            mock_response = LLMResponse(
                content="ChatGPT response",
                model="gpt-4",
                usage={"total_tokens": 100},
                finish_reason="stop"
            )
            mock_hooks.send_request = AsyncMock(return_value=mock_response)
            
            result = await send_to_chatgpt("Test prompt")
            
            assert result == "ChatGPT response"
            mock_hooks.send_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_claude(self):
        """Test send_to_claude function."""
        with patch('src.agent.hooks.llm_hooks') as mock_hooks:
            mock_response = LLMResponse(
                content="Claude response",
                model="claude-3-sonnet",
                usage={"total_tokens": 100},
                finish_reason="stop"
            )
            mock_hooks.send_request = AsyncMock(return_value=mock_response)
            
            result = await send_to_claude("Test prompt")
            
            assert result == "Claude response"
            mock_hooks.send_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_code(self):
        """Test generate_code function."""
        with patch('src.agent.hooks.llm_hooks') as mock_hooks:
            mock_response = LLMResponse(
                content="Generated code",
                model="gpt-4",
                usage={"total_tokens": 100},
                finish_reason="stop"
            )
            mock_hooks.send_code_generation_request = AsyncMock(return_value=mock_response)
            
            result = await generate_code("Add API endpoint", "FastAPI app")
            
            assert result == "Generated code"
            mock_hooks.send_code_generation_request.assert_called_once_with(
                "Add API endpoint", "FastAPI app"
            )

    @pytest.mark.asyncio
    async def test_generate_tests(self):
        """Test generate_tests function."""
        with patch('src.agent.hooks.llm_hooks') as mock_hooks:
            mock_response = LLMResponse(
                content="Generated tests",
                model="gpt-4",
                usage={"total_tokens": 100},
                finish_reason="stop"
            )
            mock_hooks.send_test_generation_request = AsyncMock(return_value=mock_response)
            
            result = await generate_tests("def test(): pass", "Add tests")
            
            assert result == "Generated tests"
            mock_hooks.send_test_generation_request.assert_called_once_with(
                "def test(): pass", "Add tests"
            )


class TestLLMHooksIntegration:
    """Integration tests for LLM hooks."""

    @pytest.mark.asyncio
    async def test_full_code_generation_flow(self):
        """Test complete code generation flow."""
        hooks = LLMHooks()
        
        # Test code generation
        code_response = await hooks.send_code_generation_request(
            "Create a simple calculator function",
            "Python application"
        )
        
        assert isinstance(code_response, LLMResponse)
        assert "calculator" in code_response.content.lower()
        
        # Test test generation for the code
        test_response = await hooks.send_test_generation_request(
            code_response.content,
            "Create a simple calculator function"
        )
        
        assert isinstance(test_response, LLMResponse)
        # The stub response doesn't contain "test" but contains "placeholder"
        assert "placeholder" in test_response.content.lower()

    @pytest.mark.asyncio
    async def test_chat_conversation_flow(self):
        """Test chat conversation flow."""
        hooks = LLMHooks()
        
        messages = [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a programming language."},
            {"role": "user", "content": "What are its main features?"}
        ]
        
        response = await hooks.send_chat_request(messages)
        
        assert isinstance(response, LLMResponse)
        assert response.model == "gpt-4"
        assert response.finish_reason == "stop" 