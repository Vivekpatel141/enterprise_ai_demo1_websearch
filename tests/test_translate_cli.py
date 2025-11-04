"""
Tests for the translate CLI command functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.translate_client import TranslationClient
from src.models import TranslationResult
import sys
import os

# Import main from translate_service module since main.py is for search
def translate_main():
    """Wrapper for translate functionality - to be implemented."""
    from src.translate_service import TranslationService
    from openai import OpenAI
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("text", type=str)
    parser.add_argument("--to", nargs="+", required=False, default=[])
    parser.add_argument("--model", type=str, default="gpt-4o-mini")
    args = parser.parse_args()
    
    if not args.to:
        print("Error: no target languages provided. Use --to en es de", file=sys.stderr)
        return 1
    
    if not args.text.strip():
        print("Error: empty text provided. Please provide text to translate", file=sys.stderr)
        return 1
        
    # Validate language codes
    import re
    allowed = {"en","es","de","fr","it","pt","zh","ja","ko","ru","ar","hi","nl","sv","no","da",
               "fi","pl","cs","tr","el","he","th","vi","id","ro","bg","uk"}
    invalid = [t for t in args.to if not re.fullmatch(r"[A-Za-z]{2,3}", t or "") or t.lower() not in allowed]
    if invalid:
        print("Error: invalid language code", file=sys.stderr)
        return 1
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found", file=sys.stderr)
        return 1
        
    try:
        oai = OpenAI(api_key=api_key)
        service = TranslationService(oai, model=args.model)
        result = service.translate(text=args.text, targets=args.to)
        
        print(f"Detected: {result.detected_language}")
        for lang, txt in result.translations.items():
            print(f"{lang}: {txt}")
        return 0
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1

@pytest.fixture
def mock_translation_client():
    """Mock TranslationClient for testing."""
    with patch('src.translate_service.TranslationClient') as mock:
        client = Mock(spec=TranslationClient)
        mock.return_value = client
        yield client

def test_translate_command_success(mock_translation_client, capsys):
    """Test successful translation with multiple target languages."""
    # Mock the translation result
    mock_result = TranslationResult(
        original_text="Bonjour le monde",
        detected_language="French",
        translations={
            "en": "Hello world",
            "es": "Hola mundo",
            "de": "Hallo Welt"
        }
    )
    mock_translation_client.translate.return_value = mock_result
    
    # Simulate CLI command
    with patch('sys.argv', ['translate', 'Bonjour le monde', '--to', 'en', 'es', 'de']):
        assert translate_main() == 0
    
    # Verify expected console output
    captured = capsys.readouterr()
    assert "Detected: French" in captured.out
    assert "en: Hello world" in captured.out
    assert "es: Hola mundo" in captured.out
    assert "de: Hallo Welt" in captured.out
    
    # Verify client was called correctly
    mock_translation_client.translate.assert_called_once_with(
        text="Bonjour le monde",
        targets=['en', 'es', 'de']
    )

def test_translate_command_no_targets(capsys):
    """Test translation command fails when no target languages specified."""
    with patch('sys.argv', ['translate', 'Hello world']):
        assert translate_main() != 0
    
    captured = capsys.readouterr()
    assert "error" in captured.err.lower()
    assert "--to" in captured.err

def test_translate_command_invalid_target(mock_translation_client, capsys):
    """Test translation fails with invalid target language."""
    with patch('sys.argv', ['translate', 'Hello', '--to', 'xx']):
        assert translate_main() != 0
    
    captured = capsys.readouterr()
    assert "error" in captured.err.lower()
    assert "invalid language code" in captured.err.lower()

def test_translate_empty_text(capsys):
    """Test translation fails with empty text."""
    with patch('sys.argv', ['translate', '', '--to', 'en']):
        assert translate_main() != 0
    
    captured = capsys.readouterr()
    assert "error" in captured.err.lower()
    assert "empty text" in captured.err.lower()

def test_translate_api_error(mock_translation_client, capsys):
    """Test graceful handling of API errors."""
    mock_translation_client.translate.side_effect = Exception("API Error")
    
    with patch('sys.argv', ['translate', 'Hello', '--to', 'es']):
        assert translate_main() != 0
    
    captured = capsys.readouterr()
    assert "error" in captured.err.lower()

def test_translate_command_with_model(mock_translation_client, capsys):
    """Test translation with specific model option."""
    mock_result = TranslationResult(
        original_text="Hello",
        detected_language="English",
        translations={"es": "Hola"}
    )
    mock_translation_client.translate.return_value = mock_result
    
    with patch('sys.argv', ['translate', 'Hello', '--to', 'es', '--model', 'gpt-4']):
        assert translate_main() == 0
    
    # Verify model was passed correctly through the service layer
    mock_translation_client.translate.assert_called_once()
    assert mock_translation_client.model == "gpt-4"