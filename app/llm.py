"""
llm.py - GrahakNyay LLM Provider Wrapper.
Supports Google Gemini and Groq.
"""

import os

from dotenv import load_dotenv
from google import genai
from groq import Groq

load_dotenv()


def generate_response(prompt):
    """Send a prompt to the selected LLM provider."""

    provider = os.getenv("LLM_PROVIDER", "gemini").lower().strip()

    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    try:
        if provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

            if not api_key:
                raise ValueError("GEMINI_API_KEY is missing in .env")

            client = genai.Client(api_key=api_key)

            response = client.models.generate_content(model=model, contents=prompt)

            result = response.text

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
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            result = response.choices[0].message.content

        else:
            raise ValueError("Invalid LLM_PROVIDER. Choose 'gemini' or 'groq'.")

        if not result or not result.strip():
            raise RuntimeError("The LLM returned an empty response.")

        return result.strip()

    except Exception as error:
        raise RuntimeError(
            f"{provider.capitalize()} API request failed: {error}"
        ) from error
