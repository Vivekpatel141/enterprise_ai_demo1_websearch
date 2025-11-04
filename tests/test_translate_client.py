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
