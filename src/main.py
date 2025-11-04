"""
Main application entry point for the web search and translation demo.

This module provides the CLI interface for both the web search
and translation features using OpenAI's API.
"""

import os
import sys
import re
import argparse
from typing import List

from dotenv import load_dotenv

from src.search_service import SearchService
from src.translate_service import TranslationService
from src.parser import ResponseParser
from src.models import (
    SearchOptions,
    SearchResult,
    Citation,
    SearchError,
)
from src.logging_config import setup_logging, get_logger, LogContext

# Load environment variables
load_dotenv()

# Initialize logging
app_logger = setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_dir=os.getenv("LOG_DIR", "logs"),
    enable_console=True,
    enable_file=True,
    json_format=os.getenv("LOG_FORMAT", "text").lower() == "json",
)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Web Search and Translation Demo using OpenAI's API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s search "What are the latest AI developments?"
  %(prog)s search "Python 3.12 new features" --model gpt-5
  %(prog)s search "climate news" --domains bbc.com,cnn.com
  %(prog)s translate "Bonjour le monde" --to en es de
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- Search command ---
    search_parser = subparsers.add_parser("search", help="Search the web")
    search_parser.add_argument("query", type=str, help="The search query")
    search_parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini)",
    )
    search_parser.add_argument(
        "--domains",
        type=str,
        help="Comma-separated list of allowed domains (e.g., 'example.com,test.com')",
    )

    # --- Translate command ---
    translate_parser = subparsers.add_parser("translate", help="Translate text")
    translate_parser.add_argument("text", type=str, help="Text to translate")
    # make --to optional here (tests expect no SystemExit and we handle it ourselves)
    translate_parser.add_argument(
        "--to",
        type=str,
        nargs="*",
        default=[],
        help="Target language codes (e.g., en es de)",
    )
    translate_parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini)",
    )

    # Global arguments
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key (can also use OPENAI_API_KEY env var)",
    )

    return parser.parse_args()


def display_results(result: SearchResult) -> None:
    """Format and display search results."""
    parser = ResponseParser()
    formatted = parser.format_for_display(result)
    print(formatted)


def format_citations(citations: List[Citation]) -> str:
    """Format citations for display."""
    if not citations:
        return "No citations found"
    return "\n".join(
        f"[{i}] {c.title} - {c.url}" for i, c in enumerate(citations, start=1)
    )


def handle_search(args: argparse.Namespace, api_key: str, logger) -> int:
    """Handle the search command."""
    logger.debug(
        f"Parsed arguments: query='{args.query}', "
        f"model={args.model}, domains={args.domains}"
    )

    if args.verbose:  # pragma: no cover
        print(f"Using model: {args.model}")
        print(f"Query: {args.query}")
        if args.domains:
            print(f"Domain filter: {args.domains}")
        print()

    # Create search options
    options = SearchOptions(model=args.model)
    if args.domains:
        domain_list = [d.strip() for d in args.domains.split(",")]
        options.allowed_domains = domain_list
        logger.info(f"Domain filtering enabled: {domain_list}")

    service = SearchService(api_key=api_key)

    if args.verbose:
        print("Searching...\n")

    logger.info(f"Executing search query: '{args.query}'")
    with LogContext(logger, "Web search", query=args.query, model=args.model):
        result = service.search(args.query, options)

    logger.info(f"Search completed: {len(result.citations)} citations found")
    display_results(result)
    return 0


def _validate_targets(targets: list[str]) -> tuple[bool, list[str]]:
    """
    Validate language codes (2–3 letters). Returns (is_valid, invalid_codes).
    """
    invalid = [t for t in targets if not re.fullmatch(r"[A-Za-z]{2,3}", t or "")]
    return (len(invalid) == 0, invalid)


def handle_translate(args: argparse.Namespace, api_key: str, logger) -> int:
    """Handle the translate command."""
    logger.debug(
        f"Parsed arguments: text='{args.text}', "
        f"targets={args.to}, model={args.model}"
    )

    # Validate input text
    if not args.text or not args.text.strip():
        logger.error("Empty text provided")
        print("Error: empty text provided. Please provide text to translate", file=sys.stderr)
        return 1

    # Validate targets present (avoid argparse SystemExit for tests)
    if not args.to:
        logger.error("No target languages provided")
        print("Error: no target languages provided. Use --to en es de", file=sys.stderr)
        return 1

    # Validate target codes (letters-only and whitelist common ISO codes)
    ok, invalid = _validate_targets(args.to)
    allowed = {
        "en","es","de","fr","it","pt","zh","ja","ko","ru","ar","hi","nl","sv","no","da",
        "fi","pl","cs","tr","el","he","th","vi","id","ro","bg","uk"
    }
    invalid = set(invalid) | {t for t in args.to if t.lower() not in allowed}
    if (not ok) or invalid:
        logger.error(f"Invalid language code(s): {sorted(invalid)}")
        print("Error: invalid language code", file=sys.stderr)
        return 1

    try:
        # Initialize OpenAI client and service
        from openai import OpenAI
        oai = OpenAI(api_key=api_key)
        service = TranslationService(oai, model=args.model)

        if args.verbose:  # pragma: no cover
            print("Translating...\n")

        logger.info(f"Translating text to {len(args.to)} languages")
        with LogContext(logger, "Translation", text=args.text, targets=args.to):
            result = service.translate(text=args.text, targets=args.to)
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1

    # Display result
    print(f"Detected: {result.detected_language}")  # TranslationClient already returns full names
    for lang, txt in result.translations.items():
        print(f"{lang}: {txt}")

    logger.info("Translation completed successfully")
    return 0


def main() -> int:
    """Main entry point."""
    logger = get_logger(__name__)

    try:
        logger.info("Application started")
        args = parse_arguments()

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        try:
            if args.command == "search":
                return handle_search(args, api_key, logger)
            elif args.command == "translate":
                return handle_translate(args, api_key, logger)
            else:
                print("Error: Please specify a command (search or translate)", file=sys.stderr)
                return 1
        except ValueError as e:
            # Catch errors from service layer
            print(f"\n❌ Error: {str(e)}", file=sys.stderr)
            return 1

    except SearchError as e:  # pragma: no cover
        logger.error(f"Search error: {e}", exc_info=True)
        print(f"\n❌ Search Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:  # pragma: no cover
        logger.error(f"Invalid input: {e}", exc_info=True)
        print(f"\n❌ Invalid Input: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:  # pragma: no cover
        logger.warning("Operation cancelled by user")
        print("\n\nOperation cancelled by user.", file=sys.stderr)
        return 130
    except Exception as e:  # pragma: no cover
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        print(f"\n❌ Unexpected Error: {e}", file=sys.stderr)
        if "args" in locals() and getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())