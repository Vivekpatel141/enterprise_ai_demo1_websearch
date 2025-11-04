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


# ============================================================================
# Interactive Mode Tests
# ============================================================================

def test_interactive_mode_single_translation():
    """Test interactive mode with single translation then exit."""
    from src.translate_main import interactive_mode
    
    # Mock user inputs: text, languages (full names), no continue
    with patch('builtins.input', side_effect=['Bonjour', 'spanish german', 'n']):
        with patch('src.translate_main.OpenAI') as MockOpenAI:
            with patch('src.translate_main.TranslationService') as MockService:
                mock_service = Mock()
                MockService.return_value = mock_service
                
                mock_result = TranslationResult(
                    original_text="Bonjour",
                    detected_language="French",
                    translations={"en": "Hello", "es": "Hola", "de": "Hallo"}
                )
                mock_service.translate.return_value = mock_result
                
                exit_code = interactive_mode("fake-key", "gpt-4o-mini", verbose=False)
                
                assert exit_code == 0
                # Verify English was added and is first
                mock_service.translate.assert_called_once()
                call_args = mock_service.translate.call_args
                assert call_args[1]['targets'][0] == 'en'
                assert 'es' in call_args[1]['targets']
                assert 'de' in call_args[1]['targets']


def test_interactive_mode_english_auto_added():
    """Test that English is automatically added to target languages."""
    from src.translate_main import ensure_english_included
    
    # Test adding English when not present
    targets = ['es', 'fr', 'de']
    result = ensure_english_included(targets)
    assert result[0] == 'en'
    assert 'es' in result
    assert 'fr' in result
    assert 'de' in result
    
    # Test moving English to front when present
    targets = ['es', 'en', 'de']
    result = ensure_english_included(targets)
    assert result[0] == 'en'
    assert result == ['en', 'es', 'de']


def test_interactive_mode_max_three_languages():
    """Test that max 3 languages are enforced in prompt."""
    from src.translate_main import prompt_for_languages
    
    # Mock user input with 4 languages (full names), should truncate to 3
    with patch('builtins.input', return_value='spanish french german italian'):
        languages = prompt_for_languages()
        assert len(languages) <= 3
        assert languages == ['es', 'fr', 'de']


def test_interactive_mode_invalid_language_retry():
    """Test that invalid language names prompt retry."""
    from src.translate_main import prompt_for_languages
    
    # First input invalid, second valid (full names)
    with patch('builtins.input', side_effect=['klingon elvish', 'spanish french']):
        languages = prompt_for_languages()
        assert languages == ['es', 'fr']
        assert 'xx' not in languages


def test_interactive_mode_empty_text_retry():
    """Test that empty text prompts retry."""
    from src.translate_main import prompt_for_text
    
    # First input empty, second valid
    with patch('builtins.input', side_effect=['', '  ', 'Hello']):
        text = prompt_for_text()
        assert text == 'Hello'


def test_interactive_mode_quit_command():
    """Test that 'q' command exits gracefully."""
    from src.translate_main import prompt_for_text
    
    with patch('builtins.input', return_value='q'):
        text = prompt_for_text()
        assert text == ''


def test_interactive_mode_multiple_translations():
    """Test interactive mode with multiple translation loop."""
    from src.translate_main import interactive_mode
    
    # Mock inputs: text1, langs1 (full names), yes, text2, langs2 (full names), no
    inputs = [
        'Bonjour',      # First text
        'spanish',      # First languages
        'y',            # Continue
        'Hello',        # Second text
        'french german',  # Second languages
        'n'             # Don't continue
    ]
    
    with patch('builtins.input', side_effect=inputs):
        with patch('src.translate_main.OpenAI'):
            with patch('src.translate_main.TranslationService') as MockService:
                mock_service = Mock()
                MockService.return_value = mock_service
                
                mock_result = TranslationResult(
                    original_text="test",
                    detected_language="English",
                    translations={"en": "test", "es": "prueba"}
                )
                mock_service.translate.return_value = mock_result
                
                exit_code = interactive_mode("fake-key", "gpt-4o-mini")
                
                assert exit_code == 0
                # Should have been called twice (two translations)
                assert mock_service.translate.call_count == 2


def test_interactive_mode_keyboard_interrupt():
    """Test that Ctrl+C exits gracefully."""
    from src.translate_main import interactive_mode
    
    with patch('builtins.input', side_effect=KeyboardInterrupt()):
        with patch('src.translate_main.OpenAI'):
            with patch('src.translate_main.TranslationService'):
                exit_code = interactive_mode("fake-key", "gpt-4o-mini")
                assert exit_code == 130


def test_prompt_continue_yes_variants():
    """Test that various 'yes' inputs are accepted."""
    from src.translate_main import prompt_continue
    
    for yes_input in ['y', 'yes', 'Y', 'YES']:
        with patch('builtins.input', return_value=yes_input):
            assert prompt_continue() is True


def test_prompt_continue_no_variants():
    """Test that various 'no' inputs are accepted."""
    from src.translate_main import prompt_continue
    
    for no_input in ['n', 'no', 'N', 'NO']:
        with patch('builtins.input', return_value=no_input):
            assert prompt_continue() is False


def test_prompt_continue_invalid_then_valid():
    """Test that invalid continue input prompts retry."""
    from src.translate_main import prompt_continue
    
    with patch('builtins.input', side_effect=['maybe', 'x', 'y']):
        assert prompt_continue() is True


def test_main_interactive_mode_no_args():
    """Test that main() enters interactive mode when no args provided."""
    from src.translate_main import main
    
    with patch('sys.argv', ['translate_main']):
        with patch('src.translate_main.interactive_mode', return_value=0) as mock_interactive:
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'fake-key'}):
                exit_code = main()
                
                assert exit_code == 0
                mock_interactive.assert_called_once()


def test_main_direct_mode_with_args():
    """Test that main() uses direct mode when args provided."""
    from src.translate_main import main
    
    with patch('sys.argv', ['translate_main', 'Hello', '--to', 'es']):
        with patch('src.translate_main.OpenAI'):
            with patch('src.translate_main.TranslationService') as MockService:
                with patch.dict(os.environ, {'OPENAI_API_KEY': 'fake-key'}):
                    mock_service = Mock()
                    MockService.return_value = mock_service
                    
                    mock_result = TranslationResult(
                        original_text="Hello",
                        detected_language="English",
                        translations={"es": "Hola"}
                    )
                    mock_service.translate.return_value = mock_result
                    
                    exit_code = main()
                    
                    assert exit_code == 0
                    mock_service.translate.assert_called_once()


def test_main_text_without_to_flag_error():
    """Test that providing text without --to flag shows helpful error."""
    from src.translate_main import main
    
    with patch('sys.argv', ['translate_main', 'Hello']):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'fake-key'}):
            exit_code = main()
            assert exit_code == 1
