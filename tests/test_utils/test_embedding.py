"""Unit tests for the embedding utility functions."""

from unittest.mock import Mock

import pytest
from openai import APIConnectionError, APIStatusError

from app.errors import ApiError, ApiErrorCode
from app.utils.embedding import generate_embedding


def test_generate_embedding_success(monkeypatch):
    """Test successful embedding generation."""
    # Arrange
    mock_settings = Mock()
    mock_settings.OPENAI_API_KEY = Mock()
    mock_settings.OPENAI_API_KEY.get_secret_value.return_value = "test-api-key"
    monkeypatch.setattr("app.utils.embedding.settings", mock_settings)

    mock_client = Mock()
    mock_openai_class = Mock(return_value=mock_client)
    monkeypatch.setattr("app.utils.embedding.openai.OpenAI", mock_openai_class)

    expected_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    mock_response = Mock()
    mock_response.data = [Mock(embedding=expected_embedding)]
    mock_client.embeddings.create.return_value = mock_response

    test_text = "This is a test text"
    test_model = "text-embedding-3-small"

    # Act
    result = generate_embedding(test_text, test_model)

    # Assert
    assert result == expected_embedding
    mock_client.embeddings.create.assert_called_once_with(model=test_model, input=test_text)
    mock_openai_class.assert_called_once_with(api_key="test-api-key")


def test_generate_embedding_missing_api_key(monkeypatch):
    """Test that ApiError is raised when OpenAI API key is missing."""
    # Arrange
    mock_settings = Mock()
    mock_settings.OPENAI_API_KEY = None
    monkeypatch.setattr("app.utils.embedding.settings", mock_settings)

    test_text = "This is a test text"

    # Act & Assert
    with pytest.raises(ApiError) as exc_info:
        generate_embedding(test_text)

    assert exc_info.value.message == "OpenAI API key is not configured"
    assert exc_info.value.error_code == ApiErrorCode.OPENAI_API_KEY_MISSING
    assert exc_info.value.http_status_code == 500


def test_generate_embedding_api_connection_error(monkeypatch):
    """Test that ApiError is raised when API connection fails."""
    # Arrange
    mock_settings = Mock()
    mock_settings.OPENAI_API_KEY = Mock()
    mock_settings.OPENAI_API_KEY.get_secret_value.return_value = "test-api-key"
    monkeypatch.setattr("app.utils.embedding.settings", mock_settings)

    mock_client = Mock()
    mock_client.embeddings.create.side_effect = APIConnectionError(
        message="Connection failed", request=Mock()
    )
    mock_openai_class = Mock(return_value=mock_client)
    monkeypatch.setattr("app.utils.embedding.openai.OpenAI", mock_openai_class)

    test_text = "This is a test text"

    # Act & Assert
    with pytest.raises(ApiError) as exc_info:
        generate_embedding(test_text)

    assert exc_info.value.message == "OpenAI API error"
    assert exc_info.value.error_code == ApiErrorCode.OPENAI_API_ERROR
    assert exc_info.value.http_status_code == 500
    assert "Connection failed" in exc_info.value.details


def test_generate_embedding_api_status_error(monkeypatch):
    """Test that ApiError is raised when API returns a status error."""
    # Arrange
    mock_settings = Mock()
    mock_settings.OPENAI_API_KEY = Mock()
    mock_settings.OPENAI_API_KEY.get_secret_value.return_value = "test-api-key"
    monkeypatch.setattr("app.utils.embedding.settings", mock_settings)

    mock_client = Mock()
    mock_client.embeddings.create.side_effect = APIStatusError(
        message="Rate limit exceeded", response=Mock(), body={}
    )
    mock_openai_class = Mock(return_value=mock_client)
    monkeypatch.setattr("app.utils.embedding.openai.OpenAI", mock_openai_class)

    test_text = "This is a test text"

    # Act & Assert
    with pytest.raises(ApiError) as exc_info:
        generate_embedding(test_text)

    assert exc_info.value.message == "OpenAI API error"
    assert exc_info.value.error_code == ApiErrorCode.OPENAI_API_ERROR
    assert exc_info.value.http_status_code == 500
    assert "Rate limit exceeded" in exc_info.value.details


def test_generate_embedding_default_model(monkeypatch):
    """Test that the default model is used when no model is specified."""
    # Arrange
    mock_settings = Mock()
    mock_settings.OPENAI_API_KEY = Mock()
    mock_settings.OPENAI_API_KEY.get_secret_value.return_value = "test-api-key"
    monkeypatch.setattr("app.utils.embedding.settings", mock_settings)

    mock_client = Mock()
    mock_openai_class = Mock(return_value=mock_client)
    monkeypatch.setattr("app.utils.embedding.openai.OpenAI", mock_openai_class)

    expected_embedding = [0.1, 0.2, 0.3]
    mock_response = Mock()
    mock_response.data = [Mock(embedding=expected_embedding)]
    mock_client.embeddings.create.return_value = mock_response

    test_text = "This is a test text"

    # Act
    result = generate_embedding(test_text)

    # Assert
    assert result == expected_embedding
    mock_client.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small", input=test_text
    )
