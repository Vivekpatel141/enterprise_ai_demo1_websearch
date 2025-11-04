import os
from .translate_parser import TranslationParser

SYSTEM_PROMPT = """You are a translation engine.
Return ONLY valid JSON with this exact schema:
{
  "detected_language": "<string>",
  "translations": { "<lang_code>": "<translated text>", ... },
  "original_text": "<optional original text>"
}
No prose. No markdown. No extra keys. JSON only."""

USER_TEMPLATE = """Detect the source language and translate the text into the following target languages: {targets}.
Text:
{text}
Return ONLY the JSON."""

class TranslationClient:
    def __init__(self, openai_client, model: str | None = None, temperature: float | None = None):
        self.client = openai_client
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = 0 if temperature is None else temperature

    def translate(self, text: str, targets: list[str]):
        targets_str = ", ".join(targets)
        user_msg = USER_TEMPLATE.format(text=text, targets=targets_str)

        resp = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=self.temperature,
        )

        raw = resp.output_text()
        return TranslationParser.parse(raw)
