
"""
llm.py - Day 06

GrahakNyay LLM Provider Wrapper.
Supports Google Gemini and Groq.
"""

import os
from dotenv import load_dotenv
from google import genai
from groq import Groq

# Load environment variables from .env
load_dotenv()


def generate_response(prompt):
    """
    Send a prompt to the selected LLM provider
    and return the generated response.
    """

    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    try:
        # ---------------- GEMINI PROVIDER ----------------
        if provider == "gemini":

            api_key = os.getenv("GEMINI_API_KEY")
            model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

            if not api_key:
                raise ValueError("GEMINI_API_KEY is missing in .env")

            client = genai.Client(api_key=api_key)

            response = client.models.generate_content(
                model=model,
                contents=prompt
            )

            return response.text

        # ---------------- GROQ PROVIDER ----------------
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
                        "content": prompt
                    }
                ],
                temperature=0.3
            )

            return response.choices[0].message.content

        else:
            raise ValueError(
                "Invalid LLM_PROVIDER. Choose 'gemini' or 'groq'."
            )

    except Exception as error:
        raise RuntimeError(
            f"{provider.capitalize()} API request failed: {error}"
        ) from error
