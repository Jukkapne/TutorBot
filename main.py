#!/usr/bin/env python3
"""Simple Gemma/Gemini API command-line demo."""

from __future__ import annotations

import json
import mimetypes
import re
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass
from getpass import getpass
from pathlib import Path
from typing import Any

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Missing dependency: google-genai")
    print("Install it with: python -m pip install -r requirements.txt")
    raise SystemExit(1)


CONFIG_PATH = Path("config.json")
DEFAULT_MODEL = ""
FILE_REQUEST_RE = re.compile(r"```tutorbot-file\s*(\{.*?\})\s*```", re.DOTALL)

SYSTEM_INSTRUCTION = """You are TutorBot, a concise command-line assistant.

If you want the program to write a local file, do not say you saved it.
Instead include a separate fenced block exactly like this:

```tutorbot-file
{"path":"outputs/example.txt","description":"Short reason for this file","content":"Full file content"}
```

The user must approve the write before the CLI saves anything.
"""


@dataclass
class AppConfig:
    api_key: str
    model: str = DEFAULT_MODEL
    output_dir: str = "outputs"
    mode: str = "standard"


def main() -> int:
    print("TutorBot - Gemma via Gemini API")
    print("Type /help for commands, /exit to quit.\n")

    config = load_or_create_config()
    client = genai.Client(api_key=config.api_key)

    available_models = list_generate_content_models(client)
    config = ensure_model_available(config, available_models)
    config = choose_session_settings(config, available_models)
    save_config(config)

    if not startup_connectivity_check(client, config):
        return 1

    print("\nReady. Write your prompt, optionally add an image when asked.\n")
    while True:
        prompt = input("Prompt> ").strip()
        if not prompt:
            continue
        if prompt in {"/exit", "/quit"}:
            print("Bye.")
            return 0
        if prompt == "/help":
            print_help()
            continue
        if prompt == "/settings":
            config = choose_session_settings(config)
            save_config(config)
            continue

        image_ref = input("Image URL/path (optional)> ").strip()
        try:
            contents = build_contents(prompt, image_ref)
            response = client.models.generate_content(
                model=config.model,
                contents=contents,
                config=build_generation_config(config),
            )
        except Exception as exc:
            print_api_error(exc)
            continue

        text = response.text or ""
        visible_text, file_requests = extract_file_requests(text)
        print("\nGemma:")
        print(visible_text.strip() or "(empty response)")
        print()

        for request in file_requests:
            handle_file_request(request, Path(config.output_dir))


def load_or_create_config() -> AppConfig:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Could not read {CONFIG_PATH}: {exc}")
            raise SystemExit(1)

        api_key = str(data.get("api_key", "")).strip()
        if not api_key:
            print(f"{CONFIG_PATH} exists but has no api_key value.")
            api_key = prompt_api_key()
            data["api_key"] = api_key
            write_config_data(data)

        return AppConfig(
            api_key=api_key,
            model=str(data.get("model") or DEFAULT_MODEL),
            output_dir=str(data.get("output_dir") or "outputs"),
            mode=str(data.get("mode") or "standard"),
        )

    print(f"No {CONFIG_PATH} found. Creating one now.")
    config = AppConfig(api_key=prompt_api_key())
    save_config(config)
    print(f"Created {CONFIG_PATH}. It is ignored by git.\n")
    return config


def prompt_api_key() -> str:
    api_key = getpass("Gemini API key from Google AI Studio: ").strip()
    if not api_key:
        print("API key is required.")
        raise SystemExit(1)
    return api_key


def save_config(config: AppConfig) -> None:
    write_config_data(
        {
            "api_key": config.api_key,
            "model": config.model,
            "mode": config.mode,
            "output_dir": config.output_dir,
        }
    )


def write_config_data(data: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def startup_connectivity_check(client: Any, config: AppConfig) -> bool:
    print(f"Checking Gemini API connectivity with model {config.model}...")
    try:
        response = client.models.generate_content(
            model=config.model,
            contents="Reply with OK.",
            config=types.GenerateContentConfig(
                system_instruction="Reply with OK and no extra text."
            ),
        )
    except Exception as exc:
        print_api_error(exc)
        return False

    text = (response.text or "").strip()
    if text:
        print(f"Connectivity OK: {text[:80]}\n")
    else:
        print("Connectivity OK, but the model returned no text.\n")
    return True


def list_generate_content_models(client: Any) -> list[str]:
    try:
        models = []
        for model in client.models.list():
            actions = list(getattr(model, "supported_actions", []) or [])
            if "generateContent" not in actions:
                continue
            name = normalize_model_name(str(getattr(model, "name", "")))
            if name:
                models.append(name)
    except Exception as exc:
        print("Could not list models for this API key.")
        print_api_error(exc)
        return []

    return sorted(set(models), key=model_sort_key)


def normalize_model_name(name: str) -> str:
    return name.removeprefix("models/").strip()


def model_sort_key(model: str) -> tuple[int, str]:
    lowered = model.lower()
    if lowered.startswith("gemma-4"):
        return (0, lowered)
    if lowered.startswith("gemma-3"):
        return (1, lowered)
    if "gemma" in lowered:
        return (2, lowered)
    return (3, lowered)


def gemma_models(models: list[str]) -> list[str]:
    return [model for model in models if "gemma" in model.lower()]


def ensure_model_available(config: AppConfig, available_models: list[str]) -> AppConfig:
    if not available_models:
        if config.model:
            return config
        print("No model list available. You can enter a model name manually.")
        model = input("Model name> ").strip()
        if not model:
            print("Model name is required.")
            raise SystemExit(1)
        return AppConfig(
            api_key=config.api_key,
            model=model,
            output_dir=config.output_dir,
            mode=config.mode,
        )

    if config.model and config.model in available_models:
        return config

    choices = gemma_models(available_models)
    if choices:
        selected = choices[0]
        if config.model:
            print(
                f"Configured model '{config.model}' is not available for this API key."
            )
        print(f"Using available Gemma model: {selected}")
    else:
        selected = available_models[0]
        print("No Gemma models were returned for this API key.")
        print(f"Using first generateContent model instead: {selected}")

    return AppConfig(
        api_key=config.api_key,
        model=selected,
        output_dir=config.output_dir,
        mode=config.mode,
    )


def choose_session_settings(config: AppConfig, available_models: list[str]) -> AppConfig:
    models = gemma_models(available_models) or available_models

    print("Model options:")
    if models:
        for index, model in enumerate(models, start=1):
            marker = " (current)" if model == config.model else ""
            print(f"  {index}. {model}{marker}")
        custom_index = len(models) + 1
        print(f"  {custom_index}. Enter custom model name")
    else:
        custom_index = 1
        print("  1. Enter custom model name")

    choice = input(f"Choose model [current: {config.model}]> ").strip()

    model = config.model
    if choice.isdigit() and models and 1 <= int(choice) <= len(models):
        model = models[int(choice) - 1]
    elif choice == str(custom_index):
        custom = input("Model name> ").strip()
        if custom:
            model = normalize_model_name(custom)
    elif choice:
        print("Unknown choice, keeping current model.")

    print("\nMode options:")
    print("  1. standard")
    print("  2. thinking-high (only for models that support thinking)")
    mode_choice = input(f"Choose mode [current: {config.mode}]> ").strip()
    mode = config.mode
    if mode_choice == "1":
        mode = "standard"
    elif mode_choice == "2":
        mode = "thinking-high"

    output_dir = input(f"Output directory [current: {config.output_dir}]> ").strip()
    return AppConfig(
        api_key=config.api_key,
        model=model,
        mode=mode,
        output_dir=output_dir or config.output_dir,
    )


def build_generation_config(config: AppConfig) -> types.GenerateContentConfig:
    kwargs: dict[str, Any] = {"system_instruction": SYSTEM_INSTRUCTION}
    if config.mode == "thinking-high":
        kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="high")
    return types.GenerateContentConfig(**kwargs)


def build_contents(prompt: str, image_ref: str) -> list[Any] | str:
    if not image_ref:
        return prompt

    image_bytes, mime_type = load_image_bytes(image_ref)
    image = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    return [prompt, image]


def load_image_bytes(image_ref: str) -> tuple[bytes, str]:
    if image_ref.startswith(("http://", "https://")):
        request = urllib.request.Request(
            image_ref, headers={"User-Agent": "TutorBot/1.0"}
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                content_type = response.headers.get_content_type()
                data = response.read()
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Could not download image URL: {exc}") from exc

        if not content_type.startswith("image/"):
            content_type = "image/jpeg"
        return data, content_type

    path = Path(image_ref).expanduser()
    if not path.exists() or not path.is_file():
        raise RuntimeError(f"Image file does not exist: {path}")

    mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    if not mime_type.startswith("image/"):
        raise RuntimeError(f"File does not look like an image: {path}")
    return path.read_bytes(), mime_type


def extract_file_requests(text: str) -> tuple[str, list[dict[str, Any]]]:
    requests: list[dict[str, Any]] = []

    def replace(match: re.Match[str]) -> str:
        raw = match.group(1)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return match.group(0)
        if isinstance(data, dict):
            requests.append(data)
            return "[TutorBot file write request hidden pending approval]"
        return match.group(0)

    visible_text = FILE_REQUEST_RE.sub(replace, text)
    return visible_text, requests


def handle_file_request(request: dict[str, Any], output_dir: Path) -> None:
    path_value = str(request.get("path") or "").strip()
    content = request.get("content")
    description = str(request.get("description") or "No description provided.").strip()

    if not path_value or not isinstance(content, str):
        print("Ignored malformed file write request.")
        return

    target = Path(path_value).expanduser()
    if not target.is_absolute():
        target = output_dir / target.name if target.parts[:1] != output_dir.parts[:1] else target

    print("\nFile write requested:")
    print(f"  Path: {target}")
    print(f"  Description: {description}")
    preview = content[:500].replace("\n", "\\n")
    print(f"  Preview: {preview}{'...' if len(content) > 500 else ''}")
    answer = input("Write this file? [y/N]> ").strip().lower()
    if answer not in {"y", "yes"}:
        print("Skipped file write.")
        return

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    except OSError as exc:
        print(f"Could not write file: {exc}")
        return
    print(f"Wrote {target}")


def print_api_error(exc: Exception) -> None:
    message = str(exc)
    redacted = redact_secrets(message)
    print("\nGemini API error:")
    print(textwrap.fill(redacted, width=88))
    print()


def redact_secrets(text: str) -> str:
    return re.sub(r"(AIza[0-9A-Za-z_-]{20,})", "AIza...REDACTED", text)


def print_help() -> None:
    print(
        """
Commands:
  /help      Show this help
  /settings  Change model, thinking mode, or output directory
  /exit      Quit

Prompt flow:
  1. Type a text prompt.
  2. Optionally provide an image URL or local image path.
  3. Review the model response.
  4. Approve or decline any file write request before it touches disk.
""".strip()
    )


if __name__ == "__main__":
    raise SystemExit(main())
