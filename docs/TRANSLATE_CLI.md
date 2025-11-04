# Translation CLI

A command-line tool for translating text into multiple languages using OpenAI's API.

## Usage

### Basic Translation

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

### With Custom Model

```bash
python -m src.translate_main "Hello world" --to fr es de --model gpt-4
```

### Verbose Mode

```bash
python -m src.translate_main "Ciao mondo" --to en fr --verbose
```

Output:
```
Using model: gpt-4o-mini
Text: Ciao mondo
Target languages: en, fr

Translating...

Detected: Italian
en: Hello world
fr: Bonjour le monde
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
