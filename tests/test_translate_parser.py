import json
import pytest
from src.models import TranslationResult
from src.translate_parser import TranslationParser

def test_parse_valid_json_payload():
    payload = {
        "detected_language": "French",
        "translations": {"en": "Hello world", "es": "Hola mundo", "de": "Hallo Welt"}
    }
    out = TranslationParser.parse(json.dumps(payload))
    assert isinstance(out, TranslationResult)
    assert out.detected_language == "French"
    assert out.translations["en"] == "Hello world"
    assert set(out.translations.keys()) == {"en", "es", "de"}

def test_parse_rejects_non_json():
    with pytest.raises(ValueError) as e:
        TranslationParser.parse("Detected: French | en: Hello world")
    assert "JSON" in str(e.value)

def test_parse_missing_required_fields():
    """Reject if detected_language or translations are missing."""
    incomplete = '{"detected_language": "English"}'
    with pytest.raises(ValueError, match="Missing required fields"):
        TranslationParser.parse(incomplete)


def test_parse_invalid_types():
    """Test that parser rejects invalid types for fields."""
    # detected_language is not a string
    invalid = '{"detected_language": 123, "translations": {"en": "Hello"}}'
    with pytest.raises(ValueError, match="Invalid types"):
        TranslationParser.parse(invalid)
    
    # translations is not a dict
    invalid2 = '{"detected_language": "French", "translations": "not a dict"}'
    with pytest.raises(ValueError, match="Invalid types"):
        TranslationParser.parse(invalid2)


def test_parse_non_dict_top_level():
    """Test that parser rejects non-dict at top level."""
    invalid = '["not", "a", "dict"]'
    with pytest.raises(ValueError, match="Expected JSON object at top level"):
        TranslationParser.parse(invalid)
