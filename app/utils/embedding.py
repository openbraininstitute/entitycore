"""Utility functions for generating embeddings using OpenAI API."""

import openai
from openai import APIConnectionError, APIStatusError

from app.config import settings
from app.errors import ApiError, ApiErrorCode


def generate_embedding(text: str, model: str = "text-embedding-3-small") -> list[float]:
    """Generate an embedding for the given text using OpenAI API.

    Args:
        text: The text to generate an embedding for
        model: The OpenAI embedding model to use (default: text-embedding-3-small)

    Returns:
        A list of floats representing the embedding vector

    Raises:
        ApiError: If OpenAI API key is not configured or API call fails
    """
    if settings.OPENAI_API_KEY is None:
        raise ApiError(
            message="OpenAI API key is not configured",
            error_code=ApiErrorCode.OPENAI_API_KEY_MISSING,
            http_status_code=401,
        )

    openai_api_key = settings.OPENAI_API_KEY.get_secret_value()

    try:
        # Generate embedding using OpenAI API
        client = openai.OpenAI(api_key=openai_api_key)
        response = client.embeddings.create(model=model, input=text)

        # Return the generated embedding
        return response.data[0].embedding

    except (APIConnectionError, APIStatusError) as e:
        raise ApiError(
            message="OpenAI API error",
            error_code=ApiErrorCode.OPENAI_API_ERROR,
            http_status_code=500,
            details=str(e),
        ) from e
