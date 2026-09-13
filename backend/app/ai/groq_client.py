import os
import time
import logging
from typing import Any, Callable
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from groq import RateLimitError, AuthenticationError, APIError

load_dotenv()

logger = logging.getLogger(__name__)

TARGET_MODEL = "gemma2-9b-it"
VERIFIED_FALLBACK_MODEL = "openai/gpt-oss-120b"

def get_runtime_model_name(requested_model: str = None) -> str:
    """
    Resolves the active Groq runtime model based on configuration and availability.
    Explicitly logs substitution when gemma2-9b-it is decommissioned.
    Never uses prohibited models.
    """
    configured_model = requested_model or os.getenv("GROQ_MODEL")

    if not configured_model or configured_model == TARGET_MODEL:
        logger.warning(
            "Groq model '%s' is decommissioned. Substituting with verified supported model '%s'.",
            TARGET_MODEL,
            VERIFIED_FALLBACK_MODEL
        )
        return VERIFIED_FALLBACK_MODEL

    # Prohibit qwen/qwen3.8-27b explicitly
    if "qwen3.8-27b" in configured_model:
        logger.warning(
            "Model '%s' is prohibited. Substituting with verified supported model '%s'.",
            configured_model,
            VERIFIED_FALLBACK_MODEL
        )
        return VERIFIED_FALLBACK_MODEL

    return configured_model


def get_groq_client(temperature: float = 0.1, model: str = None) -> ChatGroq:
    """Returns a ChatGroq LLM instance with verified runtime model configuration."""
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("groq_api")
    if not api_key:
        raise AuthenticationError("GROQ_API_KEY is not set in environment or .env file.")

    runtime_model = get_runtime_model_name(model)

    return ChatGroq(
        groq_api_key=api_key,
        model_name=runtime_model,
        temperature=temperature,
        max_retries=1,
    )


def execute_with_backoff(func: Callable[..., Any], max_retries: int = 3, base_delay: float = 2.0) -> Any:
    """
    Executes an LLM call with exponential backoff on HTTP 429 RateLimitError.
    Catches AuthenticationError (401), RateLimitError (429), and APIError (5xx) cleanly without exposing keys.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            return func()
        except AuthenticationError:
            logger.error("Groq Authentication Failure: Invalid or expired GROQ_API_KEY.")
            raise
        except RateLimitError as e:
            attempt += 1
            if attempt >= max_retries:
                logger.error("Groq rate limit (429) persisted after %d attempts.", max_retries)
                raise
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(
                "Groq Rate Limit (429) encountered. Attempt %d/%d. Backing off for %.1f seconds...",
                attempt, max_retries, delay
            )
            time.sleep(delay)
        except APIError as e:
            logger.error("Groq API provider error (status %s): %s", getattr(e, "status_code", "unknown"), str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error in LLM execution: %s", str(e))
            raise
