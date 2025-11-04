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
  # Interactive mode (default):
  %(prog)s
  
  # Direct mode with arguments:
  %(prog)s "Bonjour le monde" --to en es de
  %(prog)s "Hello world" --to fr es --model gpt-4
        """,
    )
    
    parser.add_argument(
        "text",
        type=str,
        nargs='?',  # Make text optional
        help="Text to translate (omit for interactive mode)"
    )
    
    parser.add_argument(
        "--to",
        nargs="+",
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


def prompt_for_text() -> str:
    """
    Prompt user for text to translate.
    Returns empty string if user wants to quit.
    """
    while True:
        text = input("\nEnter text to translate (or 'q' to quit): ").strip()
        
        if text.lower() in ['q', 'quit', 'exit']:
            return ''
        
        if text:
            return text
        
        print("⚠️  Text cannot be empty. Please try again.")


def prompt_for_languages() -> list[str]:
    """
    Prompt user for target languages (max 3).
    Returns list of valid language codes.
    """
    allowed = {
        "en", "es", "de", "fr", "it", "pt", "zh", "ja", "ko", "ru", "ar", "hi",
        "nl", "sv", "no", "da", "fi", "pl", "cs", "tr", "el", "he", "th", "vi",
        "id", "ro", "bg", "uk"
    }
    
    while True:
        print("\nEnter target languages (up to 3, space-separated):")
        print("Examples: es fr de | ja zh ko | ru ar hi")
        lang_input = input("Languages: ").strip().lower()
        
        if not lang_input:
            print("⚠️  Please enter at least one language code.")
            continue
        
        # Parse input
        languages = lang_input.split()
        
        # Validate codes
        invalid = [lang for lang in languages if lang not in allowed]
        if invalid:
            print(f"⚠️  Invalid language code(s): {', '.join(invalid)}")
            print(f"Valid codes: {', '.join(sorted(allowed))}")
            continue
        
        # Enforce max 3
        if len(languages) > 3:
            print(f"⚠️  Maximum 3 languages allowed. Using first 3: {', '.join(languages[:3])}")
            languages = languages[:3]
        
        return languages


def ensure_english_included(targets: list[str]) -> list[str]:
    """
    Ensure English is included in targets and appears first.
    Always returns 'en' as first element.
    """
    if 'en' in targets:
        # Move 'en' to front if present
        targets = ['en'] + [t for t in targets if t != 'en']
    else:
        # Add 'en' at front
        targets = ['en'] + targets
        print("ℹ️  Adding English (en) as default language")
    
    return targets


def prompt_continue() -> bool:
    """
    Ask if user wants to translate another phrase.
    Returns True to continue, False to exit.
    """
    while True:
        choice = input("\nTranslate another phrase? (y/n): ").strip().lower()
        
        if choice in ['y', 'yes']:
            return True
        if choice in ['n', 'no']:
            return False
        
        print("⚠️  Please enter 'y' or 'n'")


def interactive_mode(api_key: str, model: str, verbose: bool = False) -> int:
    """
    Run interactive translation mode with prompts.
    
    Args:
        api_key: OpenAI API key
        model: Model to use for translation
        verbose: Enable verbose output
        
    Returns:
        Exit code (0 for success)
    """
    logger = get_logger(__name__)
    
    print("\n🌍 Translation Tool - Interactive Mode")
    print("=" * 40)
    
    # Initialize OpenAI client and service once
    oai = OpenAI(api_key=api_key)
    service = TranslationService(oai, model=model)
    
    # Language name mapping for display
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
    
    while True:
        try:
            # Get text from user
            text = prompt_for_text()
            if not text:  # User wants to quit
                print("\nGoodbye! 👋")
                break
            
            # Get target languages
            targets = prompt_for_languages()
            
            # Always include English first
            targets = ensure_english_included(targets)
            
            # Perform translation
            if verbose:
                print(f"\nUsing model: {model}")
                print(f"Translating to: {', '.join(targets)}")
            
            print("\nTranslating...")
            logger.info(f"Translating text to {len(targets)} languages")
            result = service.translate(text=text, targets=targets)
            
            # Display results
            print()
            detected_lang = result.detected_language.lower()
            display_lang = language_names.get(detected_lang, result.detected_language)
            print(f"Detected: {display_lang}")
            
            for lang, translation in result.translations.items():
                print(f"{lang}: {translation}")
            
            logger.info("Translation completed successfully")
            
            # Ask to continue
            if not prompt_continue():
                print("\nGoodbye! 👋")
                break
                
        except ValueError as e:
            logger.error(f"Translation error: {e}")
            print(f"\n❌ Error: {str(e)}", file=sys.stderr)
            if not prompt_continue():
                print("\nGoodbye! 👋")
                break
        except KeyboardInterrupt:
            logger.warning("Translation cancelled by user")
            print("\n\nGoodbye! 👋")
            return 130
        except Exception as e:
            logger.critical(f"Unexpected error: {e}", exc_info=True)
            print(f"\n❌ Error: {str(e)}", file=sys.stderr)
            if verbose:
                import traceback
                traceback.print_exc()
            if not prompt_continue():
                print("\nGoodbye! 👋")
                break
    
    return 0


def main() -> int:
    """Main entry point for translation CLI."""
    logger = get_logger(__name__)
    
    try:
        logger.info("Translation CLI started")
        args = parse_arguments()
        
        # Get API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment")
            print("Error: OPENAI_API_KEY not found in environment variables", file=sys.stderr)
            return 1
        
        # Determine mode: interactive or direct
        # Interactive mode: no text argument provided
        # Direct mode: text argument provided with --to flag
        if not args.text:
            # Interactive mode (default)
            return interactive_mode(api_key, args.model, args.verbose)
        
        # Direct mode - validate arguments
        if not args.to:
            logger.error("--to flag required in direct mode")
            print("Error: --to flag required when providing text directly", file=sys.stderr)
            print("Try: python -m src.translate_main \"your text\" --to en es de", file=sys.stderr)
            print("Or run without arguments for interactive mode", file=sys.stderr)
            return 1
        
        # Validate input text
        if not args.text.strip():
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
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
