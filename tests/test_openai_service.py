"""Tests for OpenAI API Service."""

import pytest
import httpx
import respx
from httpx import Response


# Test data
TEST_ENDPOINT = "https://api.openai.com/v1/chat/completions"
TEST_API_KEY = "sk-test1234567890abcdef"
TEST_MESSAGE = "Hello, AI!"

MOCK_SUCCESS_RESPONSE = {
    "id": "chatcmpl-test",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "gpt-3.5-turbo",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you today?"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
}


class TestOpenAIServiceError:
    """Tests for OpenAIServiceError exception class."""

    def test_exception_with_message_only(self):
        """Test creating exception with message only."""
        from app.services.openai_service import OpenAIServiceError

        error = OpenAIServiceError("Test error message")
        assert error.message == "Test error message"
        assert error.status_code is None
        assert str(error) == "Test error message"

    def test_exception_with_status_code(self):
        """Test creating exception with message and status code."""
        from app.services.openai_service import OpenAIServiceError

        error = OpenAIServiceError("API error", status_code=401)
        assert error.message == "API error"
        assert error.status_code == 401

    def test_exception_is_exception_subclass(self):
        """Test that OpenAIServiceError is a proper Exception."""
        from app.services.openai_service import OpenAIServiceError

        assert issubclass(OpenAIServiceError, Exception)
        with pytest.raises(OpenAIServiceError):
            raise OpenAIServiceError("test")


class TestOpenAIResponse:
    """Tests for OpenAIResponse dataclass."""

    def test_response_creation(self):
        """Test creating OpenAIResponse with required fields."""
        from app.services.openai_service import OpenAIResponse

        response = OpenAIResponse(
            response_summary="Hello from AI",
            response_time_ms=150,
        )
        assert response.response_summary == "Hello from AI"
        assert response.response_time_ms == 150

    def test_response_is_dataclass(self):
        """Test that OpenAIResponse is a dataclass."""
        from dataclasses import is_dataclass

        from app.services.openai_service import OpenAIResponse

        assert is_dataclass(OpenAIResponse)


class TestSendMessage:
    """Tests for send_message function."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_send_message_success(self):
        """Test successful API call returns OpenAIResponse."""
        from app.services.openai_service import send_message, OpenAIResponse

        respx.post(TEST_ENDPOINT).mock(
            return_value=Response(200, json=MOCK_SUCCESS_RESPONSE)
        )

        result = await send_message(
            api_endpoint=TEST_ENDPOINT,
            api_key=TEST_API_KEY,
            message_content=TEST_MESSAGE,
        )

        assert isinstance(result, OpenAIResponse)
        assert result.response_summary == "Hello! How can I help you today?"
        assert result.response_time_ms >= 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_send_message_uses_bearer_auth(self):
        """Test that request uses Bearer token authentication."""
        from app.services.openai_service import send_message

        route = respx.post(TEST_ENDPOINT).mock(
            return_value=Response(200, json=MOCK_SUCCESS_RESPONSE)
        )

        await send_message(
            api_endpoint=TEST_ENDPOINT,
            api_key=TEST_API_KEY,
            message_content=TEST_MESSAGE,
        )

        assert route.called
        request = route.calls[0].request
        assert request.headers["Authorization"] == f"Bearer {TEST_API_KEY}"

    @pytest.mark.asyncio
    @respx.mock
    async def test_send_message_chat_completions_format(self):
        """Test that request body follows Chat Completions API format."""
        from app.services.openai_service import send_message
        import json

        route = respx.post(TEST_ENDPOINT).mock(
            return_value=Response(200, json=MOCK_SUCCESS_RESPONSE)
        )

        await send_message(
            api_endpoint=TEST_ENDPOINT,
            api_key=TEST_API_KEY,
            message_content=TEST_MESSAGE,
            model="gpt-4",
        )

        assert route.called
        request = route.calls[0].request
        body = json.loads(request.content)
        assert body["model"] == "gpt-4"
        assert body["messages"] == [{"role": "user", "content": TEST_MESSAGE}]

    @pytest.mark.asyncio
    @respx.mock
    async def test_send_message_default_model(self):
        """Test that default model is gpt-3.5-turbo."""
        from app.services.openai_service import send_message
        import json

        route = respx.post(TEST_ENDPOINT).mock(
            return_value=Response(200, json=MOCK_SUCCESS_RESPONSE)
        )

        await send_message(
            api_endpoint=TEST_ENDPOINT,
            api_key=TEST_API_KEY,
            message_content=TEST_MESSAGE,
        )

        request = route.calls[0].request
        body = json.loads(request.content)
        assert body["model"] == "gpt-3.5-turbo"


class TestRetryLogic:
    """Tests for retry logic with tenacity."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_network_error_triggers_retry(self):
        """Test that network errors trigger retry and eventually succeed."""
        from app.services.openai_service import send_message, OpenAIResponse

        call_count = 0

        def fail_then_succeed(request):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectError("Connection refused")
            return Response(200, json=MOCK_SUCCESS_RESPONSE)

        respx.post(TEST_ENDPOINT).mock(side_effect=fail_then_succeed)

        result = await send_message(
            api_endpoint=TEST_ENDPOINT,
            api_key=TEST_API_KEY,
            message_content=TEST_MESSAGE,
        )

        assert call_count == 3  # 2 failures + 1 success
        assert isinstance(result, OpenAIResponse)

    @pytest.mark.asyncio
    @respx.mock
    async def test_max_retries_exceeded_raises_error(self):
        """Test that exceeding max retries raises OpenAIServiceError."""
        from app.services.openai_service import send_message, OpenAIServiceError

        respx.post(TEST_ENDPOINT).mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with pytest.raises(OpenAIServiceError) as exc_info:
            await send_message(
                api_endpoint=TEST_ENDPOINT,
                api_key=TEST_API_KEY,
                message_content=TEST_MESSAGE,
            )

        assert "Network error" in exc_info.value.message
        assert exc_info.value.status_code is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_http_4xx_error_no_retry(self):
        """Test that HTTP 4xx errors are NOT retried."""
        from app.services.openai_service import send_message, OpenAIServiceError

        call_count = 0

        def count_calls(request):
            nonlocal call_count
            call_count += 1
            return Response(401, json={"error": {"message": "Invalid API key"}})

        respx.post(TEST_ENDPOINT).mock(side_effect=count_calls)

        with pytest.raises(OpenAIServiceError) as exc_info:
            await send_message(
                api_endpoint=TEST_ENDPOINT,
                api_key=TEST_API_KEY,
                message_content=TEST_MESSAGE,
            )

        assert exc_info.value.status_code == 401
        assert call_count == 1  # No retry for 4xx

    @pytest.mark.asyncio
    @respx.mock
    async def test_timeout_triggers_retry(self):
        """Test that timeout errors trigger retry."""
        from app.services.openai_service import send_message, OpenAIServiceError

        respx.post(TEST_ENDPOINT).mock(
            side_effect=httpx.TimeoutException("Connection timed out")
        )

        with pytest.raises(OpenAIServiceError) as exc_info:
            await send_message(
                api_endpoint=TEST_ENDPOINT,
                api_key=TEST_API_KEY,
                message_content=TEST_MESSAGE,
            )

        # TimeoutException is a subclass of RequestError, so it will be retried
        # After max retries, it should raise OpenAIServiceError
        assert exc_info.value.status_code is None


class TestResponseProcessing:
    """Tests for response processing and logging."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_response_summary_truncation(self):
        """Test that long responses are truncated to 500 chars."""
        from app.services.openai_service import send_message

        long_response = "A" * 1000
        mock_response = {
            **MOCK_SUCCESS_RESPONSE,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": long_response},
                    "finish_reason": "stop"
                }
            ]
        }

        respx.post(TEST_ENDPOINT).mock(return_value=Response(200, json=mock_response))

        result = await send_message(
            api_endpoint=TEST_ENDPOINT,
            api_key=TEST_API_KEY,
            message_content=TEST_MESSAGE,
        )

        assert len(result.response_summary) == 500

    @pytest.mark.asyncio
    @respx.mock
    async def test_short_response_not_truncated(self):
        """Test that short responses are not truncated."""
        from app.services.openai_service import send_message

        respx.post(TEST_ENDPOINT).mock(
            return_value=Response(200, json=MOCK_SUCCESS_RESPONSE)
        )

        result = await send_message(
            api_endpoint=TEST_ENDPOINT,
            api_key=TEST_API_KEY,
            message_content=TEST_MESSAGE,
        )

        assert result.response_summary == "Hello! How can I help you today?"

    @pytest.mark.asyncio
    @respx.mock
    async def test_response_time_recorded(self):
        """Test that response time is recorded in milliseconds."""
        from app.services.openai_service import send_message

        respx.post(TEST_ENDPOINT).mock(
            return_value=Response(200, json=MOCK_SUCCESS_RESPONSE)
        )

        result = await send_message(
            api_endpoint=TEST_ENDPOINT,
            api_key=TEST_API_KEY,
            message_content=TEST_MESSAGE,
        )

        # Response time should be a positive integer
        assert isinstance(result.response_time_ms, int)
        assert result.response_time_ms >= 0

    def test_api_key_masking(self):
        """Test that API key is properly masked."""
        from app.utils.security import mask_api_key

        # Test standard key
        masked = mask_api_key(TEST_API_KEY)
        assert masked == "sk-t...cdef"
        assert TEST_API_KEY not in masked

        # Test short key
        short_masked = mask_api_key("short")
        assert short_masked == "***"


class TestImageGenerationResponse:
    """Tests for image generation response handling."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_image_response_with_null_content(self):
        """Test that image response with null content returns image count summary."""
        from app.services.openai_service import send_message, OpenAIResponse

        image_response = {
            "id": "test",
            "object": "chat.completion",
            "created": 0,
            "model": "gemini-3-pro-image",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "images": [
                        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}, "index": 0},
                        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}, "index": 1}
                    ]
                },
                "finish_reason": "stop"
            }]
        }

        respx.post(TEST_ENDPOINT).mock(return_value=Response(200, json=image_response))

        result = await send_message(
            api_endpoint=TEST_ENDPOINT,
            api_key=TEST_API_KEY,
            message_content=TEST_MESSAGE,
        )

        assert isinstance(result, OpenAIResponse)
        assert result.response_summary == "[图像生成成功] 共 2 张图片"
        assert result.response_time_ms >= 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_image_response_single_image(self):
        """Test that single image response is handled correctly."""
        from app.services.openai_service import send_message

        image_response = {
            "id": "test",
            "object": "chat.completion",
            "created": 0,
            "model": "gemini-3-pro-image",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "images": [
                        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}, "index": 0}
                    ]
                },
                "finish_reason": "stop"
            }]
        }

        respx.post(TEST_ENDPOINT).mock(return_value=Response(200, json=image_response))

        result = await send_message(
            api_endpoint=TEST_ENDPOINT,
            api_key=TEST_API_KEY,
            message_content=TEST_MESSAGE,
        )

        assert result.response_summary == "[图像生成成功] 共 1 张图片"

    @pytest.mark.asyncio
    @respx.mock
    async def test_null_content_no_images_raises_error(self):
        """Test that null content with no images raises OpenAIServiceError."""
        from app.services.openai_service import send_message, OpenAIServiceError

        bad_response = {
            "id": "test",
            "object": "chat.completion",
            "created": 0,
            "model": "gpt-4",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None
                },
                "finish_reason": "stop"
            }]
        }

        respx.post(TEST_ENDPOINT).mock(return_value=Response(200, json=bad_response))

        with pytest.raises(OpenAIServiceError) as exc_info:
            await send_message(
                api_endpoint=TEST_ENDPOINT,
                api_key=TEST_API_KEY,
                message_content=TEST_MESSAGE,
            )

        assert "null content with no images" in exc_info.value.message

    @pytest.mark.asyncio
    @respx.mock
    async def test_null_content_empty_images_raises_error(self):
        """Test that null content with empty images array raises OpenAIServiceError."""
        from app.services.openai_service import send_message, OpenAIServiceError

        bad_response = {
            "id": "test",
            "object": "chat.completion",
            "created": 0,
            "model": "gpt-4",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "images": []
                },
                "finish_reason": "stop"
            }]
        }

        respx.post(TEST_ENDPOINT).mock(return_value=Response(200, json=bad_response))

        with pytest.raises(OpenAIServiceError) as exc_info:
            await send_message(
                api_endpoint=TEST_ENDPOINT,
                api_key=TEST_API_KEY,
                message_content=TEST_MESSAGE,
            )

        assert "null content with no images" in exc_info.value.message

    @pytest.mark.asyncio
    @respx.mock
    async def test_text_response_still_works(self):
        """Test that normal text responses still work (backward compatibility)."""
        from app.services.openai_service import send_message

        respx.post(TEST_ENDPOINT).mock(
            return_value=Response(200, json=MOCK_SUCCESS_RESPONSE)
        )

        result = await send_message(
            api_endpoint=TEST_ENDPOINT,
            api_key=TEST_API_KEY,
            message_content=TEST_MESSAGE,
        )

        assert result.response_summary == "Hello! How can I help you today?"


class TestMalformedResponses:
    """Tests for handling malformed API responses."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_malformed_json_response(self):
        """Test that malformed JSON raises OpenAIServiceError."""
        from app.services.openai_service import send_message, OpenAIServiceError

        # Return invalid JSON structure (missing choices)
        malformed_response = {"id": "test", "object": "chat.completion"}

        respx.post(TEST_ENDPOINT).mock(
            return_value=Response(200, json=malformed_response)
        )

        with pytest.raises(OpenAIServiceError) as exc_info:
            await send_message(
                api_endpoint=TEST_ENDPOINT,
                api_key=TEST_API_KEY,
                message_content=TEST_MESSAGE,
            )

        assert "Unexpected response structure" in exc_info.value.message
        assert exc_info.value.status_code == 200

    @pytest.mark.asyncio
    @respx.mock
    async def test_missing_message_content(self):
        """Test handling when message content is missing (treated as null)."""
        from app.services.openai_service import send_message, OpenAIServiceError

        # Response with missing content field (no content key at all)
        bad_response = {
            **MOCK_SUCCESS_RESPONSE,
            "choices": [{"index": 0, "message": {"role": "assistant"}}]
        }

        respx.post(TEST_ENDPOINT).mock(
            return_value=Response(200, json=bad_response)
        )

        with pytest.raises(OpenAIServiceError) as exc_info:
            await send_message(
                api_endpoint=TEST_ENDPOINT,
                api_key=TEST_API_KEY,
                message_content=TEST_MESSAGE,
            )

        # Missing content is treated as null, which requires images
        assert "null content with no images" in exc_info.value.message

    @pytest.mark.asyncio
    @respx.mock
    async def test_empty_choices_array(self):
        """Test handling when choices array is empty."""
        from app.services.openai_service import send_message, OpenAIServiceError

        bad_response = {**MOCK_SUCCESS_RESPONSE, "choices": []}

        respx.post(TEST_ENDPOINT).mock(
            return_value=Response(200, json=bad_response)
        )

        with pytest.raises(OpenAIServiceError) as exc_info:
            await send_message(
                api_endpoint=TEST_ENDPOINT,
                api_key=TEST_API_KEY,
                message_content=TEST_MESSAGE,
            )

        assert "Unexpected response structure" in exc_info.value.message

    @pytest.mark.asyncio
    @respx.mock
    async def test_http_5xx_error_no_retry(self):
        """Test that HTTP 5xx errors are NOT retried (same as 4xx)."""
        from app.services.openai_service import send_message, OpenAIServiceError

        call_count = 0

        def count_calls(request):
            nonlocal call_count
            call_count += 1
            return Response(503, json={"error": {"message": "Service unavailable"}})

        respx.post(TEST_ENDPOINT).mock(side_effect=count_calls)

        with pytest.raises(OpenAIServiceError) as exc_info:
            await send_message(
                api_endpoint=TEST_ENDPOINT,
                api_key=TEST_API_KEY,
                message_content=TEST_MESSAGE,
            )

        assert exc_info.value.status_code == 503
        assert call_count == 1  # No retry for 5xx

    @pytest.mark.asyncio
    @respx.mock
    async def test_empty_response_content(self):
        """Test handling when AI returns empty string."""
        from app.services.openai_service import send_message

        empty_response = {
            **MOCK_SUCCESS_RESPONSE,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": ""},
                    "finish_reason": "stop"
                }
            ]
        }

        respx.post(TEST_ENDPOINT).mock(
            return_value=Response(200, json=empty_response)
        )

        result = await send_message(
            api_endpoint=TEST_ENDPOINT,
            api_key=TEST_API_KEY,
            message_content=TEST_MESSAGE,
        )

        assert result.response_summary == ""
        assert result.response_time_ms >= 0
