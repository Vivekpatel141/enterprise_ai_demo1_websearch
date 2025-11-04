import json
from .models import TranslationResult

class TranslationParser:
    @staticmethod
    def parse(text: str) -> TranslationResult:
        try:
            obj = json.loads(text)
        except Exception:
            raise ValueError("Expected JSON translation payload")

        if not isinstance(obj, dict):
            raise ValueError("Expected JSON object at top level")

        if "detected_language" not in obj or "translations" not in obj:
            raise ValueError("Missing required fields: detected_language, translations")

        detected = obj["detected_language"]
        translations = obj["translations"]

        if not isinstance(detected, str) or not isinstance(translations, dict):
            raise ValueError("Invalid types for detected_language or translations")

        # Provide a default for models that require original_text
        original_text = obj.get("original_text", "")

        return TranslationResult(
            original_text=original_text,
            detected_language=detected,
            translations=translations,
        )
