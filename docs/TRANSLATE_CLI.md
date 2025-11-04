# Translation CLI

A command-line tool for translating text into multiple languages using OpenAI's API.

## Quick Start

### Interactive Mode (Default)

Simply run without arguments for an interactive prompt:

```bash
python -m src.translate_main
```

Example session:
```
🌍 Translation Tool - Interactive Mode
========================================

Enter text to translate (or 'q' to quit): Bonjour le monde

Enter target languages (up to 3, space-separated):
Examples: es fr de | ja zh ko | ru ar hi
Languages: es de
ℹ️  Adding English (en) as default language

Translating...

Detected: French
en: Hello world
es: Hola mundo
de: Hallo Welt

Translate another phrase? (y/n): y

Enter text to translate (or 'q' to quit): こんにちは

Enter target languages (up to 3, space-separated):
Examples: es fr de | ja zh ko | ru ar hi
Languages: es fr
ℹ️  Adding English (en) as default language

Translating...

Detected: Japanese
en: Hello
es: Hola
fr: Bonjour

Translate another phrase? (y/n): n

Goodbye! 👋
```

### Direct Mode (With Arguments)

For one-off translations or scripting:

```bash
python -m src.translate_main "Bonjour le monde" --to en es de
```

Output:
```
Detected: French
en: Hello world
es: Hola mundo
de: Hallo Welt
```

## Usage

### Interactive Mode Features

- **No arguments required** - Just run the command
- **Sequential prompts** - Easy to follow, one step at a time
- **English always included** - Automatically added as default language
- **English appears first** - Standardized output ordering
- **Max 3 languages** - Keeps costs low and output readable
- **Input validation** - Clear error messages and retry prompts
- **Multiple translations** - Loop to translate many phrases
- **Quick exit** - Type 'q', 'quit', or 'exit' anytime, or Ctrl+C

### Direct Mode Options

```bash
python -m src.translate_main [TEXT] --to [LANG1 LANG2 ...] [OPTIONS]
```

**Required:**
- `TEXT` - Text to translate (quoted if contains spaces)
- `--to` - Target language codes (space-separated)

**Optional:**
- `--model` - OpenAI model to use (default: gpt-4o-mini)
- `--verbose` - Enable verbose output
- `--help` - Show help message

### Examples

**Japanese to multiple languages:**
```bash
python -m src.translate_main "こんにちは世界" --to en es fr
```

**Arabic with custom model:**
```bash
python -m src.translate_main "مرحبا" --to en de --model gpt-4
```

**Russian with verbose output:**
```bash
python -m src.translate_main "Привет" --to en fr --verbose
```

Output:
```
Using model: gpt-4o-mini
Text: Привет
Target languages: en, fr

Translating...

Detected: Russian
en: Hello
fr: Bonjour
```

## Supported Language Codes

- **en** - English
- **es** - Spanish  
- **de** - German
- **fr** - French
- **it** - Italian
- **pt** - Portuguese
- **zh** - Chinese
- **ja** - Japanese
- **ko** - Korean
- **ru** - Russian
- **ar** - Arabic
- **hi** - Hindi
- **nl** - Dutch
- **sv** - Swedish
- **no** - Norwegian
- **da** - Danish
- **fi** - Finnish
- **pl** - Polish
- **cs** - Czech
- **tr** - Turkish
- **el** - Greek
- **he** - Hebrew
- **th** - Thai
- **vi** - Vietnamese
- **id** - Indonesian
- **ro** - Romanian
- **bg** - Bulgarian
- **uk** - Ukrainian

## Environment Variables

The CLI requires the following environment variables:

- `OPENAI_API_KEY` (required) - Your OpenAI API key
- `OPENAI_MODEL` (optional) - Default model to use (defaults to `gpt-4o-mini`)
- `LOG_LEVEL` (optional) - Logging level (defaults to `INFO`)
- `LOG_DIR` (optional) - Directory for log files (defaults to `logs`)

## Error Handling

The CLI validates:
- Empty text input
- Invalid language codes
- Missing API key
- API errors

All errors are reported to stderr with clear error messages.

## Exit Codes

- `0` - Success
- `1` - Error (validation, API, or other)
- `130` - Cancelled by user (Ctrl+C)
