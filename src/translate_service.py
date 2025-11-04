from typing import List
from src.translate_client import TranslationClient
from src.models import TranslationResult

class TranslationService:
    """
    Thin wrapper around TranslationClient to keep main() clean.
    Important: forward keyword arguments so tests can assert_called_with(text=..., targets=...).
    """

    def __init__(self, openai_client=None, model: str | None = None):
        """Initialize with either an OpenAI client or a pre-configured TranslationClient."""
        # Check if openai_client is already a client instance (has translate method)
        if hasattr(openai_client, 'translate') and callable(getattr(openai_client, 'translate')):
            # Already a TranslationClient instance (possibly a mock)
            self.client = openai_client
        else:
            # It's an OpenAI client, wrap it with TranslationClient
            self.client = TranslationClient(openai_client, model=model)
        
        # Always set model attribute (important for tests and tracking)
        if model is not None:
            self.client.model = model
        
        self.model = model

    def translate(self, *, text: str, targets: List[str]) -> TranslationResult:
        """
        Translate text to targets via the underlying client.
        Note: keyword-only signature (*,) enforces use of kwargs at call sites.
        Raises ValueError on any API or parsing error.
        """
        try:
            return self.client.translate(text=text, targets=targets)
        except Exception as e:
            raise ValueError(f"Translation API error: {str(e)}")
