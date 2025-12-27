"""OpenAI API Service with Retry Logic."""

import time
from dataclasses import dataclass
from typing import Any

import httpx
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.utils.security import mask_api_key


class OpenAIServiceError(Exception):
    """Exception raised when OpenAI API call fails."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


@dataclass
class OpenAIResponse:
    """Response from OpenAI API call."""

    response_summary: str  # First 500 chars of AI response
    response_time_ms: int  # Request duration in milliseconds


# HTTP timeout configuration
REQUEST_TIMEOUT = 30.0  # seconds


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.RequestError),
    reraise=True,
)
async def _make_request(
    client: httpx.AsyncClient,
    endpoint: str,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> httpx.Response:
    """Make HTTP request with retry logic.

    Only retries on network errors (httpx.RequestError).
    Does not retry on HTTP 4xx/5xx errors.
    """
    response = await client.post(endpoint, headers=headers, json=payload)
    return response


async def send_message(
    api_endpoint: str,
    api_key: str,
    message_content: str,
    model: str = "gpt-3.5-turbo",
) -> OpenAIResponse:
    """Send a message to OpenAI API.

    Args:
        api_endpoint: The OpenAI API endpoint URL.
        api_key: The API key (plain text, already decrypted).
        message_content: The message to send.
        model: The model to use (default: gpt-3.5-turbo).

    Returns:
        OpenAIResponse with response summary and timing.

    Raises:
        OpenAIServiceError: If the API call fails after retries.
    """
    masked_key = mask_api_key(api_key)
    logger.info(f"Sending message to OpenAI API (key: {masked_key})")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": message_content}],
    }

    start_time = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await _make_request(client, api_endpoint, headers, payload)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        # Check for HTTP errors
        if response.status_code >= 400:
            error_detail = response.text[:500] if response.text else "No error details"
            logger.error(
                f"OpenAI API error: {response.status_code} - {error_detail} "
                f"(key: {masked_key})"
            )
            raise OpenAIServiceError(
                message=f"API returned {response.status_code}: {error_detail}",
                status_code=response.status_code,
            )

        # Parse successful response
        try:
            data = response.json()
            message = data["choices"][0]["message"]
            ai_content = message.get("content")

            # Handle image generation responses (content=null with images array)
            if ai_content is None:
                images = message.get("images")
                if isinstance(images, list) and images:
                    ai_content = f"[图像生成成功] 共 {len(images)} 张图片"
                    logger.info(
                        f"Image generation response detected: {len(images)} images "
                        f"(key: {masked_key})"
                    )
                else:
                    raise OpenAIServiceError(
                        message="API returned null content with no images",
                        status_code=response.status_code,
                    )
        except OpenAIServiceError:
            raise
        except (KeyError, IndexError, TypeError) as e:
            logger.error(
                f"OpenAI API returned unexpected response structure: {e} "
                f"(key: {masked_key})"
            )
            raise OpenAIServiceError(
                message=f"Unexpected response structure: {str(e)}",
                status_code=response.status_code,
            ) from e
        except Exception as e:
            logger.error(
                f"Failed to parse OpenAI API response: {e} "
                f"(key: {masked_key})"
            )
            raise OpenAIServiceError(
                message=f"Failed to parse response: {str(e)}",
                status_code=response.status_code,
            ) from e

        response_summary = ai_content[:500] if len(ai_content) > 500 else ai_content

        logger.info(
            f"OpenAI API call successful in {elapsed_ms}ms "
            f"(key: {masked_key})"
        )

        return OpenAIResponse(
            response_summary=response_summary,
            response_time_ms=elapsed_ms,
        )

    except httpx.RequestError as e:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        logger.error(
            f"OpenAI API network error after {elapsed_ms}ms: {e} "
            f"(key: {masked_key})"
        )
        raise OpenAIServiceError(
            message=f"Network error: {str(e)}",
            status_code=None,
        ) from e
