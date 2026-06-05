# TutorBot

Simple Python command-line demo for using Google Gemma through the Gemini API with a Google AI Studio API key.

## Setup

1. Get a Gemini API key from Google AI Studio.
2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Run:

```bash
python main.py
```

On first run, TutorBot creates `config.json` and asks for your API key. `config.json` is ignored by git.

## What It Does

- Connects to Gemma models through the Gemini API.
- Checks connectivity when the program starts.
- Lets you choose the model and standard or high-thinking mode when the selected model supports it.
- Accepts text prompts.
- Accepts an optional image URL or local image path after each prompt.
- Requires approval before writing any model-requested file to disk.

## Notes

- Default model: `gemma-3-27b-it`, matching Google's Gemma-on-Gemini API example.
- You can enter a custom model name at startup if Google AI Studio exposes another model for your key.
- Generated files are written only after approval and default to `outputs/`, which is ignored by git.
- This is intentionally a simple `python main.py` demo, not a packaged application.
