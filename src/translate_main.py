"""
Translation CLI entry point.

Usage:
    python -m src.translate_main "Bonjour le monde" --to en es de
"""

import os
import sys
import re
import argparse
from dotenv import load_dotenv
from openai import OpenAI

from src.translate_service import TranslationService
from src.logging_config import setup_logging, get_logger

# Load environment variables
load_dotenv()

# Initialize logging
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_dir=os.getenv("LOG_DIR", "logs"),
    enable_console=True,
    enable_file=True,
    json_format=os.getenv("LOG_FORMAT", "text").lower() == "json",
)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for translation."""
    parser = argparse.ArgumentParser(
        description="Translation CLI using OpenAI's API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Bonjour le monde" --to en es de
  %(prog)s "Hello world" --to fr es --model gpt-4
        """,
    )
    
    parser.add_argument(
        "text",
        type=str,
        help="Text to translate"
    )
    
    parser.add_argument(
        "--to",
        nargs="+",
        required=True,
        help="Target language codes (e.g., en es de)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        help="OpenAI model to use (default: gpt-4o-mini)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point for translation CLI."""
    logger = get_logger(__name__)
    
    try:
        logger.info("Translation CLI started")
        args = parse_arguments()
        
        # Validate input text
        if not args.text or not args.text.strip():
            logger.error("Empty text provided")
            print("Error: empty text provided. Please provide text to translate", file=sys.stderr)
            return 1
        
        # Validate language codes
        allowed = {
            "en", "es", "de", "fr", "it", "pt", "zh", "ja", "ko", "ru", "ar", "hi",
            "nl", "sv", "no", "da", "fi", "pl", "cs", "tr", "el", "he", "th", "vi",
            "id", "ro", "bg", "uk"
        }
        invalid = [
            t for t in args.to 
            if not re.fullmatch(r"[A-Za-z]{2,3}", t or "") or t.lower() not in allowed
        ]
        if invalid:
            logger.error(f"Invalid language code(s): {sorted(invalid)}")
            print("Error: invalid language code", file=sys.stderr)
            return 1
        
        # Get API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment")
            print("Error: OPENAI_API_KEY not found in environment variables", file=sys.stderr)
            return 1
        
        # Initialize OpenAI client and service
        if args.verbose:
            print(f"Using model: {args.model}")
            print(f"Text: {args.text}")
            print(f"Target languages: {', '.join(args.to)}")
            print("\nTranslating...\n")
        
        oai = OpenAI(api_key=api_key)
        service = TranslationService(oai, model=args.model)
        
        # Perform translation
        logger.info(f"Translating text to {len(args.to)} languages")
        result = service.translate(text=args.text, targets=args.to)
        
        # Map language codes to full names for display
        language_names = {
            'fr': 'French', 'en': 'English', 'es': 'Spanish', 'de': 'German',
            'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian',
            'zh': 'Chinese', 'ja': 'Japanese', 'ko': 'Korean', 'ar': 'Arabic',
            'hi': 'Hindi', 'nl': 'Dutch', 'sv': 'Swedish', 'no': 'Norwegian',
            'da': 'Danish', 'fi': 'Finnish', 'pl': 'Polish', 'cs': 'Czech',
            'tr': 'Turkish', 'el': 'Greek', 'he': 'Hebrew', 'th': 'Thai',
            'vi': 'Vietnamese', 'id': 'Indonesian', 'ro': 'Romanian',
            'bg': 'Bulgarian', 'uk': 'Ukrainian'
        }
        detected_lang = result.detected_language.lower()
        display_lang = language_names.get(detected_lang, result.detected_language)
        
        # Display results
        print(f"Detected: {display_lang}")
        for lang, text in result.translations.items():
            print(f"{lang}: {text}")
        
        logger.info("Translation completed successfully")
        return 0
        
    except ValueError as e:
        logger.error(f"Translation error: {e}")
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        logger.warning("Translation cancelled by user")
        print("\n\nTranslation cancelled by user.", file=sys.stderr)
        return 130
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        print(f"Error: {str(e)}", file=sys.stderr)
        if args.verbose if 'args' in locals() else False:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
