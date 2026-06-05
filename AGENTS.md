<!-- GSD:project-start source:PROJECT.md -->

## Project

**TutorBot**

TutorBot is a simple Python command-line program that demonstrates how to connect to Google's free-tier Gemma LLM access through the Gemini API using an API key from Google AI Studio. It runs as a single `main.py` script for v1, lets the user choose applicable Gemma/Gemini API modes such as flash or thinking modes when available, accepts text prompts plus optional image URL or local image file input, and prints the model response in the terminal.

The tool is for developers and learners who want a clear, practical example of using Gemma through the Gemini API without building a full application framework.

**Core Value:** Users can run one simple Python script, configure their Gemini API key, choose an available Gemma mode, send text or image prompts, and see the LLM response safely.

### Constraints

- **Tech stack**: Python script-first implementation — v1 should run from `main.py` without packaging.
- **Provider**: Google Gemini API with a Google AI Studio API key — keeps the demo focused and easy to follow.
- **Model scope**: Gemma-focused v1 — avoid general multi-provider architecture until there is a real need.
- **Interface**: Command-line interactive shell — the primary flow is repeated prompt entry after startup.
- **Input modes**: Text prompts plus optional image URL or local image path — picture analysis is part of the first release.
- **Safety**: Always confirm local file writes — protects the user's filesystem and makes model-suggested actions visible.
- **Configuration**: Store API key and useful paths/settings in a local config file — avoids hardcoding secrets in source.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->

## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
