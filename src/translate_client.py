from __future__ import annotations
from typing import Any, List

from .models import TranslationResult
from .translate_parser import TranslationParser


SYSTEM_PROMPT = (
    "You are a translation engine. Detect the language of the provided text and "
    "return translations ONLY as strict JSON with keys: original_text, detected_language, translations. "
    "The `translations` object must use the provided target language codes as keys. "
    "DO NOT include any extra commentary or code fences."
)


class TranslationClient:
    """
    Calls the OpenAI Responses API to perform detection + multi-target translation.
    Robust to different SDK return shapes (output_text method vs property, etc.).
    """

    def __init__(self, openai_client: Any, model: str | None = None, temperature: float | None = None):
        self.client = openai_client
        self.model = model or "gpt-4o-mini"
        self.temperature = 0 if temperature is None else float(temperature)

    def _extract_text(self, resp: Any) -> str:
        """
        Extract raw text from a Responses API result in a shape-agnostic way.

        Tries (in order):
          1) resp.output_text()          # callable
          2) resp.output_text            # string property
          3) resp.output[0].content[0].text  # older structured shape
          4) str(resp)                   # last resort
        """
        # 1) Method form
        if hasattr(resp, "output_text") and callable(getattr(resp, "output_text")):
            try:
                return resp.output_text()
            except TypeError:
                # In some environments, output_text is actually a string, not callable
                pass

        # 2) Property form
        if hasattr(resp, "output_text"):
            ot = getattr(resp, "output_text")
            if isinstance(ot, str):
                return ot

        # 3) Structured fallback
        try:
            output = getattr(resp, "output", None)
            if isinstance(output, list) and output:
                content = getattr(output[0], "content", None)
                if isinstance(content, list) and content:
                    # content[0].text (object attr) or content[0]["text"] (dict-like)
                    maybe = getattr(content[0], "text", None)
                    if isinstance(maybe, str):
                        return maybe
                    if isinstance(content[0], dict) and isinstance(content[0].get("text"), str):
                        return content[0]["text"]
        except Exception:
            pass

        # 4) Last-resort
        return str(resp)

    def translate(self, *, text: str, targets: List[str]) -> TranslationResult:
        """
        Detect language of `text` and translate into each language in `targets`.

        The model MUST return strict JSON:
        {
          "original_text": "...",
          "detected_language": "English",
          "translations": { "en": "Hello world", ... }
        }
        """
        user_prompt = (
            f'Text: "{text}"\n'
            f"Targets (space-separated codes): {' '.join(targets)}"
        )

        resp = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.temperature,
        )

        raw = self._extract_text(resp)
        return TranslationParser.parse(raw)