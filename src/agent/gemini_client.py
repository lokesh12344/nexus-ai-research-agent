from google import genai
from google.genai import types
from google.api_core.exceptions import GoogleAPIError
from src.utils.config import Settings
from src.utils.logging import logger
from typing import Type, TypeVar, Optional
import pydantic
import asyncio
import time

T = TypeVar("T", bound=pydantic.BaseModel)

class GeminiClient:
    def __init__(self, settings: Settings):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_id = settings.GEMINI_MODEL

    async def _execute_with_retry_and_timeout(self, coro_func, deadline: Optional[float] = None, max_retries: int = 3, timeout: float = 30.0):
        attempt = 0
        backoff = 2.0

        while attempt < max_retries:
            # Check overall deadline
            if deadline and time.time() >= deadline:
                raise TimeoutError("Overall research deadline exceeded before Gemini call.")

            attempt += 1
            try:
                # Apply per-call timeout
                return await asyncio.wait_for(coro_func(), timeout=timeout)
            except asyncio.TimeoutError as te:
                logger.warning(f"Gemini call timed out on attempt {attempt}/{max_retries}: {te}")
                if attempt >= max_retries:
                    raise TimeoutError(f"Gemini call exceeded timeout after {max_retries} attempts.") from te
            except (GoogleAPIError, Exception) as e:
                error_msg = str(e)
                # Check for non-retryable errors (auth, invalid request)
                if "401" in error_msg or "403" in error_msg or "INVALID_ARGUMENT" in error_msg or "API_KEY" in error_msg:
                    logger.error(f"Non-retryable Gemini error: {e}")
                    raise

                # Check for rate limit / quota (429 or RESOURCE_EXHAUSTED)
                is_rate_limit = "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower()
                if is_rate_limit:
                    logger.warning(f"Gemini rate limit encountered on attempt {attempt}/{max_retries}: {e}")
                else:
                    logger.warning(f"Gemini transient error on attempt {attempt}/{max_retries}: {e}")

                if attempt >= max_retries:
                    raise

                # Check deadline before sleeping
                if deadline and time.time() >= deadline:
                    raise TimeoutError("Overall research deadline exceeded during Gemini retry backoff.")

                sleep_time = min(backoff, (deadline - time.time()) if deadline else backoff)
                if sleep_time <= 0:
                    raise TimeoutError("Overall research deadline exceeded.")

                await asyncio.sleep(sleep_time)
                backoff *= 2.0

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_instruction: Optional[str] = None,
        deadline: Optional[float] = None,
        timeout: float = 30.0
    ) -> T:
        """Generate a response validated by a Pydantic model with deadline & rate limit handling."""
        logger.debug(f"Generating structured output for model: {response_model.__name__}")

        async def _call():
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=response_model,
                ),
            )
            return response.parsed

        return await self._execute_with_retry_and_timeout(_call, deadline=deadline, timeout=timeout)

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        deadline: Optional[float] = None,
        timeout: float = 30.0
    ) -> str:
        """Generate plain text response with deadline & rate limit handling."""
        async def _call():
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                ),
            )
            return response.text

        return await self._execute_with_retry_and_timeout(_call, deadline=deadline, timeout=timeout)
