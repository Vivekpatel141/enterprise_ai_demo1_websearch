"""
Tests for translate_service.py
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.translate_service import TranslationService
from src.models import TranslationResult


def test_service_with_translation_client():
    """Test service initialization with a TranslationClient instance."""
    mock_client = Mock()
    mock_client.translate = Mock(return_value=TranslationResult(
        original_text="Hello",
        detected_language="English",
        translations={"es": "Hola"}
    ))
    
    service = TranslationService(mock_client)
    result = service.translate(text="Hello", targets=["es"])
    
    assert result.detected_language == "English"
    assert result.translations["es"] == "Hola"
    mock_client.translate.assert_called_once_with(text="Hello", targets=["es"])


def test_service_with_openai_client():
    """Test service initialization with an OpenAI client that creates a TranslationClient."""
    # Create a mock that explicitly does NOT have a 'translate' attribute
    mock_oai_client = MagicMock(spec=['responses', 'models'])
    
    # Patch the TranslationClient class so service creates our mock
    with patch('src.translate_service.TranslationClient') as MockClient:
        mock_client_instance = Mock()
        mock_client_instance.translate = Mock(return_value=TranslationResult(
            original_text="Hello",
            detected_language="English",
            translations={"es": "Hola"}
        ))
        MockClient.return_value = mock_client_instance
        
        service = TranslationService(mock_oai_client, model="gpt-4")
        result = service.translate(text="Hello", targets=["es"])
        
        # Verify TranslationClient was created with correct args
        MockClient.assert_called_once_with(mock_oai_client, model="gpt-4")
        assert result.detected_language == "English"
        assert result.translations["es"] == "Hola"


def test_service_sets_model_on_client():
    """Test that service passes the model parameter to TranslationClient."""
    with patch('src.translate_service.TranslationClient') as MockClient:
        # Create a mock that explicitly does NOT have a 'translate' attribute
        mock_oai_client = MagicMock(spec=['responses', 'models'])
        
        service = TranslationService(mock_oai_client, model="gpt-4o")
        
        # Verify the model was passed to TranslationClient
        MockClient.assert_called_once_with(mock_oai_client, model="gpt-4o")


def test_service_translate_error_handling():
    """Test that service wraps exceptions from client."""
    mock_client = Mock()
    mock_client.translate = Mock(side_effect=RuntimeError("API error"))
    
    service = TranslationService(mock_client)
    
    with pytest.raises(ValueError) as exc_info:
        service.translate(text="Hello", targets=["es"])
    
    assert "Translation failed" in str(exc_info.value)
    assert "API error" in str(exc_info.value)


def test_service_sets_model_on_client():
    """Test that service sets model attribute on client."""
    mock_client = Mock()
    mock_client.translate = Mock(return_value=TranslationResult(
        original_text="Hello",
        detected_language="English",
        translations={"es": "Hola"}
    ))
    
    service = TranslationService(mock_client, model="gpt-4")
    
    assert hasattr(mock_client, 'model')
    assert mock_client.model == "gpt-4"
    assert service.model == "gpt-4"


def test_service_translate_error_handling():
    """Test that service wraps exceptions in ValueError."""
    mock_client = Mock()
    mock_client.translate = Mock(side_effect=Exception("API Error"))
    
    service = TranslationService(mock_client)
    
    with pytest.raises(ValueError) as exc_info:
        service.translate(text="Hello", targets=["es"])
    
    assert "Translation API error" in str(exc_info.value)
    assert "API Error" in str(exc_info.value)
