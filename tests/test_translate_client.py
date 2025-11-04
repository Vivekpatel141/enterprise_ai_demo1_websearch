import json
from unittest.mock import MagicMock
from src.translate_client import TranslationClient

def _fake_resp(json_payload: dict):
    class DummyResp:
        def output_text(self):
            return json.dumps(json_payload)
    return DummyResp()

def test_translate_happy_path_monolingual_targets(monkeypatch):
    # Arrange: build a fake OpenAI client
    fake_openai = MagicMock()
    # JSON the model must return (STRICT JSON)
    payload = {
        "detected_language": "French",
        "translations": {
            "en": "Hello world",
            "es": "Hola mundo"
        }
    }
    fake_openai.responses.create.return_value = _fake_resp(payload)

    client = TranslationClient(openai_client=fake_openai, model="gpt-4o-mini")

    # Act
    result = client.translate("Bonjour le monde", targets=["en", "es"])

    # Assert
    assert result.detected_language == "French"
    assert result.translations["en"] == "Hello world"
    # ensure prompt contains the targets string in order
    args, kwargs = fake_openai.responses.create.call_args
    user_msg = kwargs["input"][1]["content"]
    assert "en, es" in user_msg

def test_translate_uses_env_default_model(monkeypatch):
    # Arrange
    fake_openai = MagicMock()
    payload = {
        "detected_language": "French",
        "translations": {"en": "Hello world"}
    }
    fake_openai.responses.create.return_value = _fake_resp(payload)

    # Provide env OPENAI_MODEL
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")

    client = TranslationClient(openai_client=fake_openai, model=None)

    # Act
    client.translate("Bonjour le monde", targets=["en"])

    # Assert model was taken from env
    _, kwargs = fake_openai.responses.create.call_args
    assert kwargs["model"] == "gpt-4o-mini"

def test_translate_sets_temperature_zero(monkeypatch):
    fake_openai = MagicMock()
    payload = {
        "detected_language": "French",
        "translations": {"en": "Hello world"}
    }
    fake_openai.responses.create.return_value = _fake_resp(payload)

    client = TranslationClient(openai_client=fake_openai)
    client.translate("Salut", targets=["en"])

    _, kwargs = fake_openai.responses.create.call_args
    assert kwargs["temperature"] == 0


def test_extract_text_with_string_property():
    """Test _extract_text with output_text as a string property."""
    fake_openai = MagicMock()
    
    class RespWithStringProperty:
        output_text = '{"detected_language": "English", "translations": {"es": "Hola"}}'
    
    fake_openai.responses.create.return_value = RespWithStringProperty()
    
    client = TranslationClient(openai_client=fake_openai)
    result = client.translate("Hello", targets=["es"])
    
    assert result.detected_language == "English"
    assert result.translations["es"] == "Hola"


def test_extract_text_with_structured_fallback():
    """Test _extract_text with structured output format."""
    fake_openai = MagicMock()
    
    class Content:
        text = '{"detected_language": "English", "translations": {"es": "Hola"}}'
    
    class Output:
        content = [Content()]
    
    class RespWithStructured:
        output = [Output()]
    
    fake_openai.responses.create.return_value = RespWithStructured()
    
    client = TranslationClient(openai_client=fake_openai)
    result = client.translate("Hello", targets=["es"])
    
    assert result.detected_language == "English"
    assert result.translations["es"] == "Hola"


def test_extract_text_with_dict_content():
    """Test _extract_text with dict-style content."""
    fake_openai = MagicMock()
    
    class Output:
        content = [{"text": '{"detected_language": "English", "translations": {"es": "Hola"}}'}]
    
    class RespWithDict:
        output = [Output()]
    
    fake_openai.responses.create.return_value = RespWithDict()
    
    client = TranslationClient(openai_client=fake_openai)
    result = client.translate("Hello", targets=["es"])
    
    assert result.detected_language == "English"
    assert result.translations["es"] == "Hola"


def test_extract_text_fallback_to_str():
    """Test _extract_text fallback to str() when all else fails."""
    fake_openai = MagicMock()
    
    # An object with no recognizable structure
    fake_openai.responses.create.return_value = '{"detected_language": "English", "translations": {"es": "Hola"}}'
    
    client = TranslationClient(openai_client=fake_openai)
    result = client.translate("Hello", targets=["es"])
    
    assert result.detected_language == "English"
    assert result.translations["es"] == "Hola"


def test_translate_with_keyword_text_argument():
    """Test translate() with text as keyword argument."""
    fake_openai = MagicMock()
    payload = {
        "detected_language": "French",
        "translations": {"en": "Hello world"}
    }
    fake_openai.responses.create.return_value = _fake_resp(payload)
    
    client = TranslationClient(openai_client=fake_openai)
    # Call with text as keyword
    result = client.translate(text="Bonjour", targets=["en"])
    
    assert result.detected_language == "French"
    assert result.translations["en"] == "Hello world"


def test_extract_text_with_output_text_property_causing_typeerror():
    """Test _extract_text when calling output_text() raises TypeError."""
    fake_openai = MagicMock()
    
    # Create a mock response where output_text is callable but raises TypeError
    class Output:
        content = [{"text": '{"detected_language": "English", "translations": {"es": "Hola"}}'}]
    
    class RespWithTypeError:
        def output_text(self):
            raise TypeError("Not callable")
        output = [Output()]
    
    fake_openai.responses.create.return_value = RespWithTypeError()
    
    client = TranslationClient(openai_client=fake_openai)
    result = client.translate("Hello", targets=["es"])
    
    # Should fall through to structured fallback
    assert result.detected_language == "English"
    assert result.translations["es"] == "Hola"


def test_extract_text_generic_exception_in_structured_fallback():
    """Test _extract_text when structured parsing raises an exception."""
    from unittest.mock import PropertyMock
    
    fake_openai = MagicMock()
    
    # Create a mock response that has no valid extraction paths
    # and will raise exception in structured fallback
    class RespWithException:
        pass
    
    resp = RespWithException()
    # Make output raise an exception when accessed
    type(resp).output = PropertyMock(side_effect=RuntimeError("No output"))
    
    fake_openai.responses.create.return_value = resp
    
    client = TranslationClient(openai_client=fake_openai)
    # Should fall back to str(resp) which will fail parsing, but that's expected
    try:
        result = client.translate("Hello", targets=["es"])
        # If we get here, str(resp) happened to be valid JSON somehow
        assert False, "Should have raised ValueError"
    except ValueError:
        # Expected - str(resp) is not valid JSON
        pass


