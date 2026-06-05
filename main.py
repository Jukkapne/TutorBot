#!/usr/bin/env python3
# This line tells the operating system to run this file with Python 3

"""Simple Gemma/Gemini API command-line demo.."""
# This is a docstring (documentation string) that describes what this program does

# Import statements: These bring in pre-built Python tools (libraries) that we'll use
from __future__ import annotations  # Allows us to use modern type hints in our code

import json          # For reading and writing JSON files (a common data format)
import mimetypes     # Helps identify file types (like .jpg, .png) by their name
import re            # Regular expressions - for finding patterns in text
import textwrap      # For formatting text into neat paragraphs
import urllib.error  # For handling errors when downloading from the internet
import urllib.request # For downloading content from URLs
from dataclasses import dataclass  # A tool for creating simple data storage classes
from getpass import getpass        # For securely reading passwords (hides what you type)
from pathlib import Path           # Modern way to work with file paths
from typing import Any             # For type hints - helps document what type of data we expect

# Try to import the Google Gemini AI library
# If it's not installed, we'll show a helpful error message
try:
    from google import genai        # Main Google AI library
    from google.genai import types  # Data types used by the Google AI library
except ImportError:  # This happens when the library is not installed
    print("Missing dependency: google-genai")
    print("Install it with: python -m pip install -r requirements.txt")
    raise SystemExit(1)  # Exit the program with error code 1


# Constants: These are values that don't change during the program's execution
CONFIG_PATH = Path("config.json")  # Where we save the user's settings (API key, model choice, etc.)
DEFAULT_MODEL = ""  # Empty string means we'll pick a model automatically later

# This is a "regular expression" pattern that finds special file-write requests in the AI's response
# It looks for text like: ```tutorbot-file {"path":"...", "content":"..."}```
FILE_REQUEST_RE = re.compile(r"```tutorbot-file\s*(\{.*?\})\s*```", re.DOTALL)

# Instructions we give to the AI model so it knows how to behave
SYSTEM_INSTRUCTION = """You are TutorBot, a concise command-line assistant.

If you want the program to write a local file, do not say you saved it.
Instead include a separate fenced block exactly like this:

```tutorbot-file
{"path":"outputs/example.txt","description":"Short reason for this file","content":"Full file content"}
```

The user must approve the write before the CLI saves anything.
"""


# @dataclass is a decorator that creates a simple class for storing data
# This is like a container that holds related pieces of information together
@dataclass
class AppConfig:
    """Stores the application's configuration settings."""
    api_key: str             # The secret key to access Google's AI (required)
    model: str = DEFAULT_MODEL      # Which AI model to use (has a default value)
    output_dir: str = "outputs"     # Where to save files the AI creates
    mode: str = "standard"          # Standard or thinking mode for the AI


def main() -> int:
    """The main function - this is where the program starts running.
    
    Returns:
        int: 0 if successful, 1 if there was an error
    """
    # Show a welcome message
    print("TutorBot - Gemma via Gemini API")
    print("Type /help for commands, /exit to quit.\n")

    # Load the configuration (settings) from file, or create a new one if it doesn't exist
    config = load_or_create_config()
    
    # Create a client object that will talk to Google's AI service
    client = genai.Client(api_key=config.api_key)

    # Get a list of AI models that we can use with our API key
    available_models = list_generate_content_models(client)
    
    # Make sure we have a valid model selected
    config = ensure_model_available(config, available_models)
    
    # Let the user choose their settings (model, mode, output directory)
    config = choose_session_settings(config, available_models)
    
    # Save the updated settings to the config file
    save_config(config)

    # Test that we can connect to the AI service
    if not startup_connectivity_check(client, config):
        return 1  # Exit with error code if connection failed

    print("\nReady. Write your prompt, optionally add an image when asked.\n")
    
    # Main loop: keep asking for prompts until the user types /exit
    while True:
        # Get user input and remove extra spaces from beginning/end
        prompt = input("Prompt> ").strip()
        
        # If they pressed Enter without typing anything, ask again
        if not prompt:
            continue
            
        # Check if user wants to exit
        if prompt in {"/exit", "/quit"}:
            print("Bye.")
            return 0  # Exit successfully
            
        # Check if user wants help
        if prompt == "/help":
            print_help()
            continue  # Go back to the start of the loop
            
        # Check if user wants to change settings
        if prompt == "/settings":
            config = choose_session_settings(config, available_models)
            save_config(config)
            continue

        # Ask if they want to include an image (optional)
        image_ref = input("Image URL/path (optional)> ").strip()
        
        # Try to send the request to the AI
        try:
            # Prepare the content (text + optional image)
            contents = build_contents(prompt, image_ref)
            
            # Send the request to the AI and get a response
            response = client.models.generate_content(
                model=config.model,
                contents=contents,
                config=build_generation_config(config),
            )
        except Exception as exc:  # If anything goes wrong, show the error
            print_api_error(exc)
            continue  # Go back and ask for a new prompt

        # Get the text from the AI's response
        text = response.text or ""
        
        # Check if the AI wants to save any files (and separate that from the visible text)
        visible_text, file_requests = extract_file_requests(text)
        
        # Show the AI's response to the user
        print("\nGemma:")
        print(visible_text.strip() or "(empty response)")
        print()

        # If the AI requested to save any files, handle each request
        for request in file_requests:
            handle_file_request(request, Path(config.output_dir))


def load_or_create_config() -> AppConfig:
    """Load configuration from file, or create a new one if it doesn't exist.
    
    Returns:
        AppConfig: The loaded or newly created configuration
    """
    # Check if the config file already exists
    if CONFIG_PATH.exists():
        # Try to read and parse the JSON file
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            # If we can't read it, show error and exit
            print(f"Could not read {CONFIG_PATH}: {exc}")
            raise SystemExit(1)

        # Get the API key from the file (if it exists)
        api_key = str(data.get("api_key", "")).strip()
        
        # If there's no API key in the file, ask the user for one
        if not api_key:
            print(f"{CONFIG_PATH} exists but has no api_key value.")
            api_key = prompt_api_key()
            data["api_key"] = api_key
            write_config_data(data)

        # Create and return an AppConfig object with the loaded settings
        return AppConfig(
            api_key=api_key,
            model=str(data.get("model") or DEFAULT_MODEL),
            output_dir=str(data.get("output_dir") or "outputs"),
            mode=str(data.get("mode") or "standard"),
        )

    # If config file doesn't exist, create a new one
    print(f"No {CONFIG_PATH} found. Creating one now.")
    config = AppConfig(api_key=prompt_api_key())  # Ask user for API key
    save_config(config)  # Save to file
    print(f"Created {CONFIG_PATH}. It is ignored by git.\n")
    return config


def prompt_api_key() -> str:
    """Ask the user to type their API key securely (won't show on screen).
    
    Returns:
        str: The API key entered by the user
    """
    # getpass hides what the user types (like a password field)
    api_key = getpass("Gemini API key from Google AI Studio: ").strip()
    
    # If they didn't enter anything, exit the program
    if not api_key:
        print("API key is required.")
        raise SystemExit(1)
    
    return api_key


def save_config(config: AppConfig) -> None:
    """Save the configuration settings to the config.json file.
    
    Args:
        config: The AppConfig object containing settings to save
    """
    # Convert the config object to a dictionary and save it
    write_config_data(
        {
            "api_key": config.api_key,
            "model": config.model,
            "mode": config.mode,
            "output_dir": config.output_dir,
        }
    )


def write_config_data(data: dict[str, Any]) -> None:
    """Write a dictionary to the config file as JSON.
    
    Args:
        data: Dictionary containing configuration data
    """
    # json.dumps converts the dictionary to a JSON string
    # indent=2 makes it pretty and readable with 2-space indentation
    CONFIG_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def startup_connectivity_check(client: Any, config: AppConfig) -> bool:
    """Test if we can successfully connect to the AI service.
    
    Args:
        client: The Google AI client object
        config: Configuration containing the model name to test
    
    Returns:
        bool: True if connection works, False if it fails
    """
    print(f"Checking Gemini API connectivity with model {config.model}...")
    
    # Try to send a simple test message
    try:
        response = client.models.generate_content(
            model=config.model,
            contents="Reply with OK.",  # Simple test prompt
            config=types.GenerateContentConfig(
                system_instruction="Reply with OK and no extra text."
            ),
        )
    except Exception as exc:  # If it fails, show the error
        print_api_error(exc)
        return False  # Connection failed

    # If we got a response, show it
    text = (response.text or "").strip()
    if text:
        print(f"Connectivity OK: {text[:80]}\n")  # Show first 80 characters
    else:
        print("Connectivity OK, but the model returned no text.\n")
    
    return True  # Connection succeeded


def list_generate_content_models(client: Any) -> list[str]:
    """Get a list of AI models available with the current API key.
    
    Args:
        client: The Google AI client object
    
    Returns:
        list[str]: List of model names that can generate content
    """
    try:
        models = []  # Start with an empty list
        
        # Loop through all available models
        for model in client.models.list():
            # Check what this model can do
            actions = list(getattr(model, "supported_actions", []) or [])
            
            # We only want models that can "generate content" (create text responses)
            if "generateContent" not in actions:
                continue  # Skip this model
            
            # Get the model's name and clean it up
            name = normalize_model_name(str(getattr(model, "name", "")))
            if name:
                models.append(name)  # Add to our list
                
    except Exception as exc:  # If listing fails, show error
        print("Could not list models for this API key.")
        print_api_error(exc)
        return []  # Return empty list

    # Remove duplicates with set(), then sort them in a smart order
    return sorted(set(models), key=model_sort_key)


def normalize_model_name(name: str) -> str:
    """Clean up a model name by removing the 'models/' prefix.
    
    Args:
        name: Raw model name (e.g., 'models/gemma-2b')
    
    Returns:
        str: Cleaned name (e.g., 'gemma-2b')
    """
    # Remove 'models/' from the beginning if it exists
    return name.removeprefix("models/").strip()


def model_sort_key(model: str) -> tuple[int, str]:
    """Determine the sort order for models (Gemma models first, newest first).
    
    Args:
        model: Model name to sort
    
    Returns:
        tuple: (priority_number, model_name) - lower numbers come first
    """
    lowered = model.lower()  # Convert to lowercase for comparison
    
    # Return a tuple: (priority, name)
    # Python sorts tuples by comparing the first element, then second, etc.
    if lowered.startswith("gemma-4"):
        return (0, lowered)  # Highest priority: Gemma 4
    if lowered.startswith("gemma-3"):
        return (1, lowered)  # Second priority: Gemma 3
    if "gemma" in lowered:
        return (2, lowered)  # Third priority: Other Gemma models
    return (3, lowered)      # Lowest priority: Non-Gemma models


def gemma_models(models: list[str]) -> list[str]:
    """Filter a list to include only Gemma models.
    
    Args:
        models: List of all model names
    
    Returns:
        list[str]: Only the models that have 'gemma' in their name
    """
    # This is a "list comprehension" - a compact way to filter a list
    # It means: "keep each model if 'gemma' is in its lowercase name"
    return [model for model in models if "gemma" in model.lower()]


def ensure_model_available(config: AppConfig, available_models: list[str]) -> AppConfig:
    """Make sure we have a valid model selected that we can actually use.
    
    Args:
        config: Current configuration
        available_models: List of models we can use with this API key
    
    Returns:
        AppConfig: Updated configuration with a valid model
    """
    # If we couldn't get the list of models from the API
    if not available_models:
        # If we already have a model configured, keep using it
        if config.model:
            return config
        # Otherwise, ask the user to type a model name
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

    # If the configured model is in the available list, we're good!
    if config.model and config.model in available_models:
        return config

    # Try to find a Gemma model to use
    choices = gemma_models(available_models)
    if choices:
        selected = choices[0]  # Pick the first Gemma model
        if config.model:
            print(
                f"Configured model '{config.model}' is not available for this API key."
            )
        print(f"Using available Gemma model: {selected}")
    else:
        # No Gemma models available, use the first available model instead
        selected = available_models[0]
        print("No Gemma models were returned for this API key.")
        print(f"Using first generateContent model instead: {selected}")

    # Return a new config with the selected model
    return AppConfig(
        api_key=config.api_key,
        model=selected,
        output_dir=config.output_dir,
        mode=config.mode,
    )


def choose_session_settings(config: AppConfig, available_models: list[str] = None) -> AppConfig:
    """Let the user choose their preferred model, mode, and output directory.
    
    Args:
        config: Current configuration
        available_models: List of models available (optional)
    
    Returns:
        AppConfig: Updated configuration with user's choices
    """
    # Prefer Gemma models, but show all models if no Gemma available
    if available_models:
        models = gemma_models(available_models) or available_models
    else:
        models = []

    # Show the available models to choose from
    print("Model options:")
    if models:
        # enumerate gives us both the index and the item from the list
        for index, model in enumerate(models, start=1):  # Start counting at 1
            marker = " (current)" if model == config.model else ""
            print(f"  {index}. {model}{marker}")
        custom_index = len(models) + 1
        print(f"  {custom_index}. Enter custom model name")
    else:
        custom_index = 1
        print("  1. Enter custom model name")

    # Get the user's choice
    choice = input(f"Choose model [current: {config.model}]> ").strip()

    model = config.model  # Start with current model
    
    # Check if they typed a number and it's in the valid range
    if choice.isdigit() and models and 1 <= int(choice) <= len(models):
        model = models[int(choice) - 1]  # Lists start at 0, so subtract 1
    elif choice == str(custom_index):  # They want to enter a custom name
        custom = input("Model name> ").strip()
        if custom:
            model = normalize_model_name(custom)
    elif choice:  # They typed something we don't understand
        print("Unknown choice, keeping current model.")

    # Now ask about the mode (standard or thinking)
    print("\nMode options:")
    print("  1. standard")
    print("  2. thinking-high (only for models that support thinking)")
    mode_choice = input(f"Choose mode [current: {config.mode}]> ").strip()
    
    mode = config.mode  # Start with current mode
    if mode_choice == "1":
        mode = "standard"
    elif mode_choice == "2":
        mode = "thinking-high"

    # Ask about output directory
    output_dir = input(f"Output directory [current: {config.output_dir}]> ").strip()
    
    # Return a new config with all the updated settings
    return AppConfig(
        api_key=config.api_key,
        model=model,
        mode=mode,
        output_dir=output_dir or config.output_dir,  # Use current if empty
    )


def build_generation_config(config: AppConfig) -> types.GenerateContentConfig:
    """Create the configuration object for generating AI responses.
    
    Args:
        config: Application configuration
    
    Returns:
        GenerateContentConfig: Configuration for the AI model
    """
    # kwargs means "keyword arguments" - a dictionary of settings
    kwargs: dict[str, Any] = {"system_instruction": SYSTEM_INSTRUCTION}
    
    # If thinking mode is enabled, add thinking configuration
    if config.mode == "thinking-high":
        kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="high")
    
    # ** unpacks the dictionary into keyword arguments
    return types.GenerateContentConfig(**kwargs)


def build_contents(prompt: str, image_ref: str) -> list[Any] | str:
    """Prepare the content to send to the AI (text + optional image).
    
    Args:
        prompt: The text prompt from the user
        image_ref: URL or file path to an image (empty string if no image)
    
    Returns:
        Either just the text prompt, or a list containing [prompt, image]
    """
    # If no image was provided, just return the text
    if not image_ref:
        return prompt

    # Load the image data from URL or file
    image_bytes, mime_type = load_image_bytes(image_ref)
    
    # Create an image object that the API understands
    image = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    
    # Return both the text and the image
    return [prompt, image]


def load_image_bytes(image_ref: str) -> tuple[bytes, str]:
    """Load image data from either a URL or a local file.
    
    Args:
        image_ref: Either a URL (http://...) or a file path
    
    Returns:
        tuple: (image_data_as_bytes, mime_type like 'image/jpeg')
    """
    # Check if it's a URL (starts with http:// or https://)
    if image_ref.startswith(("http://", "https://")):
        # Create a request with a User-Agent header (some websites require this)
        request = urllib.request.Request(
            image_ref, headers={"User-Agent": "TutorBot/1.0"}
        )
        try:
            # Download the image with a 20 second timeout
            with urllib.request.urlopen(request, timeout=20) as response:
                content_type = response.headers.get_content_type()
                data = response.read()  # Read all the bytes
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Could not download image URL: {exc}") from exc

        # Make sure it's an image type
        if not content_type.startswith("image/"):
            content_type = "image/jpeg"  # Default to JPEG if unsure
        return data, content_type

    # It's a local file path
    path = Path(image_ref).expanduser()  # expanduser handles ~ (home directory)
    
    # Check if the file exists
    if not path.exists() or not path.is_file():
        raise RuntimeError(f"Image file does not exist: {path}")

    # Guess the file type from its extension (.jpg, .png, etc.)
    mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    if not mime_type.startswith("image/"):
        raise RuntimeError(f"File does not look like an image: {path}")
    
    # Read and return the file contents
    return path.read_bytes(), mime_type


def extract_file_requests(text: str) -> tuple[str, list[dict[str, Any]]]:
    """Find and extract file write requests from the AI's response.
    
    The AI might include special blocks like:
    ```tutorbot-file
    {"path":"test.txt", "content":"Hello"}
    ```
    
    Args:
        text: The full text response from the AI
    
    Returns:
        tuple: (text_without_file_blocks, list_of_file_requests)
    """
    requests: list[dict[str, Any]] = []  # Store file requests here

    # This function will be called for each match found by the regex
    def replace(match: re.Match[str]) -> str:
        """Replace each file request block with a placeholder message."""
        raw = match.group(1)  # Get the JSON part: {"path":..., "content":...}
        try:
            # Try to parse it as JSON
            data = json.loads(raw)
        except json.JSONDecodeError:  # If it's not valid JSON, keep it as-is
            return match.group(0)
        
        # If it's a valid dictionary, save it and hide it from the user
        if isinstance(data, dict):
            requests.append(data)
            return "[TutorBot file write request hidden pending approval]"
        return match.group(0)

    # Replace all file request blocks in the text
    visible_text = FILE_REQUEST_RE.sub(replace, text)
    
    return visible_text, requests


def handle_file_request(request: dict[str, Any], output_dir: Path) -> None:
    """Ask the user if they want to save a file that the AI created.
    
    Args:
        request: Dictionary with 'path', 'content', and 'description' keys
        output_dir: Default directory for output files
    """
    # Get the file path, content, and description from the request
    path_value = str(request.get("path") or "").strip()
    content = request.get("content")
    description = str(request.get("description") or "No description provided.").strip()

    # Make sure we have valid data
    if not path_value or not isinstance(content, str):
        print("Ignored malformed file write request.")
        return

    # Convert to a Path object and handle ~ (home directory)
    target = Path(path_value).expanduser()
    
    # If it's not an absolute path, put it in the output directory
    if not target.is_absolute():
        target = output_dir / target.name if target.parts[:1] != output_dir.parts[:1] else target

    # Show the user what will be written
    print("\nFile write requested:")
    print(f"  Path: {target}")
    print(f"  Description: {description}")
    
    # Show a preview of the content (first 500 characters, with newlines shown as \\n)
    preview = content[:500].replace("\n", "\\n")
    print(f"  Preview: {preview}{'...' if len(content) > 500 else ''}")
    
    # Ask for permission
    answer = input("Write this file? [y/N]> ").strip().lower()
    if answer not in {"y", "yes"}:
        print("Skipped file write.")
        return

    # Try to write the file
    try:
        # Create the parent directories if they don't exist
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the content to the file
        target.write_text(content, encoding="utf-8")
    except OSError as exc:  # If something goes wrong (no permission, etc.)
        print(f"Could not write file: {exc}")
        return
    
    print(f"Wrote {target}")


def print_api_error(exc: Exception) -> None:
    """Display an error message from the API, hiding any secrets.
    
    Args:
        exc: The exception (error) that occurred
    """
    message = str(exc)  # Convert the exception to a string
    redacted = redact_secrets(message)  # Hide any API keys in the message
    
    print("\nGemini API error:")
    # textwrap.fill breaks long text into multiple lines (max 88 characters per line)
    print(textwrap.fill(redacted, width=88))
    print()


def redact_secrets(text: str) -> str:
    """Replace API keys in text with a placeholder to keep them secret.
    
    Args:
        text: Text that might contain API keys
    
    Returns:
        str: Text with API keys replaced with 'AIza...REDACTED'
    """
    # This regex pattern matches Google API keys (they start with 'AIza')
    # We replace them so they don't appear in error messages
    return re.sub(r"(AIza[0-9A-Za-z_-]{20,})", "AIza...REDACTED", text)


def print_help() -> None:
    """Display help information about how to use TutorBot."""
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


# This special check means: "only run this code if this file is run directly"
# (not if it's imported as a module by another file)
if __name__ == "__main__":
    # Call the main function and exit with its return code (0 = success, 1 = error)
    raise SystemExit(main())
