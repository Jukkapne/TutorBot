# TutorBot

## What This Is

TutorBot is a simple Python command-line program that demonstrates how to connect to Google's free-tier Gemma LLM access through the Gemini API using an API key from Google AI Studio. It runs as a single `main.py` script for v1, lets the user choose applicable Gemma/Gemini API modes such as flash or thinking modes when available, accepts text prompts plus optional image URL or local image file input, and prints the model response in the terminal.

The tool is for developers and learners who want a clear, practical example of using Gemma through the Gemini API without building a full application framework.

## Core Value

Users can run one simple Python script, configure their Gemini API key, choose an available Gemma mode, send text or image prompts, and see the LLM response safely.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Provide a simple `main.py` entry point that can be run directly with Python.
- [ ] Store the Gemini API key and relevant local settings in a configuration file.
- [ ] Connect to Google Gemma models through the Gemini API using a Google AI Studio API key.
- [ ] Offer an interactive command-line flow for selecting the model or mode when the API supports multiple applicable options.
- [ ] Accept user-entered text prompts.
- [ ] Accept optional image input from either a URL or a local file path for picture analysis.
- [ ] Display LLM responses clearly in the terminal.
- [ ] Detect or represent model-requested file/document output as proposed file operations.
- [ ] Require explicit user approval before writing any image, document, or generated content to disk.
- [ ] Keep v1 focused on Gemma/Gemini API demonstration rather than a packaged Python application.

### Out of Scope

- Installing as a Python package or exposing a console script — v1 should remain a simple `python main.py` style program.
- Multi-provider LLM support — v1 focuses on Google Gemma through the Gemini API.
- Building a GUI, web app, or chatbot server — the first release is command-line only.
- Automatic file writes without confirmation — local disk writes must be explicitly approved by the user.

## Context

The project should teach by example: the code needs to be understandable, runnable, and explicit about where the Gemini API key comes from and how requests are sent. The expected key source is Google AI Studio. The target model family for v1 is Gemma exposed through the Gemini API, with mode selection limited to what the API and selected model actually support.

The command-line experience should be interactive first. A user should be able to launch `main.py`, configure or load their API key, choose an applicable model or mode, enter prompts, optionally attach an image URL or local path, and continue prompting until they exit.

Image analysis should support both remote image URLs and local image file paths. The implementation should handle invalid or missing image inputs gracefully.

The program must treat file writing as a privileged action. If the model response implies that an image, document, or other generated file should be saved locally, the tool should show the proposed path and a concise content summary or preview, then ask for permission before writing.

## Constraints

- **Tech stack**: Python script-first implementation — v1 should run from `main.py` without packaging.
- **Provider**: Google Gemini API with a Google AI Studio API key — keeps the demo focused and easy to follow.
- **Model scope**: Gemma-focused v1 — avoid general multi-provider architecture until there is a real need.
- **Interface**: Command-line interactive shell — the primary flow is repeated prompt entry after startup.
- **Input modes**: Text prompts plus optional image URL or local image path — picture analysis is part of the first release.
- **Safety**: Always confirm local file writes — protects the user's filesystem and makes model-suggested actions visible.
- **Configuration**: Store API key and useful paths/settings in a local config file — avoids hardcoding secrets in source.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Build v1 as a single `main.py` script | The goal is a clear demonstration program, not a distributable package yet | — Pending |
| Focus v1 on Gemma through the Gemini API | Keeps the example aligned with the intended free-tier Google AI Studio setup | — Pending |
| Use an interactive command-line shell first | The user wants to choose modes and enter prompts naturally from the terminal | — Pending |
| Support both image URLs and local image files | Picture analysis should work with common user input sources | — Pending |
| Require confirmation before all disk writes | Model-generated file operations should never modify the filesystem silently | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-05 after initialization*
