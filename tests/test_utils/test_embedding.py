"""Unit tests for the embedding utility functions."""

from unittest.mock import Mock, patch

import pytest
from openai import APIConnectionError, APIStatusError

from app.db.model import EmbeddingMixin
from app.errors import ApiError, ApiErrorCode
from app.utils import embedding as test_module


def test_settings():
    with patch("app.utils.embedding.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = None

        with pytest.raises(ApiError, match="OpenAI API key is not configured"):
            test_module.generate_embedding("test text")

    with patch("app.utils.embedding.settings") as mock_settings:
        mock_key = Mock()
        mock_key.get_secret_value.return_value = "random"
        mock_settings.OPENAI_API_KEY = mock_key

        res = test_module.generate_embedding("test text")

        assert isinstance(res, list)
        assert len(res) == EmbeddingMixin.SIZE


def test_generate_embedding_success(monkeypatch):
    """Test successful embedding generation."""
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

    result = test_module.generate_embedding(test_text, test_model)

    assert result == expected_embedding
    mock_client.embeddings.create.assert_called_once_with(model=test_model, input=test_text)
    mock_openai_class.assert_called_once_with(api_key="test-api-key")

    # Test that the default model is used when no model is specified
    mock_client.reset_mock()
    result = test_module.generate_embedding(test_text)

    assert result == expected_embedding
    mock_client.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small", input=test_text
    )


def test_generate_embedding_missing_api_key(monkeypatch):
    """Test that ApiError is raised when OpenAI API key is missing."""
    mock_settings = Mock()
    mock_settings.OPENAI_API_KEY = None
    monkeypatch.setattr("app.utils.embedding.settings", mock_settings)

    test_text = "This is a test text"

    with pytest.raises(ApiError) as exc_info:
        test_module.generate_embedding(test_text)

    assert exc_info.value.message == "OpenAI API key is not configured"
    assert exc_info.value.error_code == ApiErrorCode.OPENAI_API_KEY_MISSING
    assert exc_info.value.http_status_code == 500


def test_generate_embedding_api_connection_error(monkeypatch):
    """Test that ApiError is raised when API connection fails."""
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

    with pytest.raises(ApiError) as exc_info:
        test_module.generate_embedding("This is a test text")

    assert exc_info.value.message == "OpenAI API error"
    assert exc_info.value.error_code == ApiErrorCode.OPENAI_API_ERROR
    assert exc_info.value.http_status_code == 500
    assert "Connection failed" in exc_info.value.details


def test_generate_embedding_api_status_error(monkeypatch):
    """Test that ApiError is raised when API returns a status error."""
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

    with pytest.raises(ApiError) as exc_info:
        test_module.generate_embedding("This is a test text")

    assert exc_info.value.message == "OpenAI API error"
    assert exc_info.value.error_code == ApiErrorCode.OPENAI_API_ERROR
    assert exc_info.value.http_status_code == 500
    assert "Rate limit exceeded" in exc_info.value.details


def test__pseudo_random_embedding():
    a = test_module.pseudo_random_embedding("test")
    b = test_module.pseudo_random_embedding("test")
    assert all(-1.0 <= v <= 1.0 for v in a)
    assert len(a) == EmbeddingMixin.SIZE
    assert a == b

    a = test_module.pseudo_random_embedding("")
    assert all(-1.0 <= v <= 1.0 for v in a)
    assert len(a) == EmbeddingMixin.SIZE
