"""Utility functions for generating embeddings using OpenAI API."""

import openai

from app.config import settings


def generate_embedding(text: str, model: str = "text-embedding-3-small") -> list[float]:
    """Generate an embedding for the given text using OpenAI API.

    Args:
        text: The text to generate an embedding for
        model: The OpenAI embedding model to use (default: text-embedding-3-small)

    Returns:
        A list of floats representing the embedding vector

    Raises:
        ValueError: If OpenAI API key is not configured
    """
    if settings.OPENAI_API_KEY is None:
        message = "OpenAI API key is not configured."
        raise ValueError(message)

    openai_api_key = settings.OPENAI_API_KEY.get_secret_value()

    # Generate embedding using OpenAI API
    client = openai.OpenAI(api_key=openai_api_key)
    response = client.embeddings.create(model=model, input=text)

    # Return the generated embedding
    return response.data[0].embedding
