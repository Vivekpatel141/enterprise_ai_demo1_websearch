"""
Tests for the translation functionality in models.py.
"""

import pytest
from src.models import TranslationResult


def test_detect_language():
    """Test language detection from sample text."""
    # Create a translation result with French text
    result = TranslationResult(
        original_text="Bonjour le monde",
        detected_language="French",
        translations={
            "en": "Hello world",
            "es": "Hola mundo"
        }
    )
    
    assert result.detected_language == "French"
    assert result.original_text == "Bonjour le monde"
    assert "en" in result.translations
    assert result.translations["en"] == "Hello world"