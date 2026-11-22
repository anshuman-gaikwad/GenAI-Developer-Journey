
"""
llm.py - GrahakNyay LLM Provider Wrapper.
Supports Google Gemini and Groq.
"""

import logging
import os
import time

from dotenv import load_dotenv
from google import genai
from groq import Groq

load_dotenv()

logger = logging.getLogger(__name__)


def generate_response(prompt):
    """Send a prompt to the selected LLM provider."""

    provider = os.getenv("LLM_PROVIDER", "gemini").lower().strip()

    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    start_time = time.perf_counter()
    input_tokens = None
    output_tokens = None

    try:
        if provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

            if not api_key:
                raise ValueError("GEMINI_API_KEY is missing in .env")

            client = genai.Client(api_key=api_key)

            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )

            result = response.text

            # Gemini token usage
            usage = getattr(response, "usage_metadata", None)

            if usage is not None:
                input_tokens = getattr(
                    usage, "prompt_token_count", None
                )
                output_tokens = getattr(
                    usage, "candidates_token_count", None
                )

        elif provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            model = os.getenv("GROQ_MODEL")

            if not api_key:
                raise ValueError("GROQ_API_KEY is missing in .env")

            if not model:
                raise ValueError("GROQ_MODEL is missing in .env")

            client = Groq(api_key=api_key)

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.3,
            )

            result = response.choices[0].message.content

            # Groq token usage
            usage = getattr(response, "usage", None)

            if usage is not None:
                input_tokens = getattr(
                    usage, "prompt_tokens", None
                )
                output_tokens = getattr(
                    usage, "completion_tokens", None
                )

        else:
            raise ValueError(
                "Invalid LLM_PROVIDER. Choose 'gemini' or 'groq'."
            )

        if not result or not result.strip():
            raise RuntimeError("The LLM returned an empty response.")

        # Measure LLM request latency in milliseconds
        latency_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

        # Log metadata only, not prompts or API keys
        logger.info(
            "llm_request provider=%s model=%s "
            "latency_ms=%.2f input_tokens=%s output_tokens=%s",
            provider,
            model,
            latency_ms,
            input_tokens,
            output_tokens,
        )

        return result.strip()

    except Exception as error:
        logger.exception(
            "llm_request_failed provider=%s",
            provider,
        )

        raise RuntimeError(
            f"{provider.capitalize()} API request failed: {error}"
        ) from error
