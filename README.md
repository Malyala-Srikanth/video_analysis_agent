# Video Analysis Agent (Standalone)

A **standalone analysis agent** for visual verification of test steps using multimodal LLMs (e.g., GPT-4o).

> **Note:** Input files (`agent_inner_thoughts.json`, `feature_result.html`) are generated by [testzeus-hercules](https://github.com/test-zeus-ai/testzeus-hercules) or a compatible test runner.

## Overview

- Parses planned test steps and test result HTML
- Extracts frames from video proof
- Uses a multimodal LLM to verify if each step is visually observed
- Outputs a deviation report for each step

## Folder Structure

```
video_analysis_agent/
├── agent/
│   ├── __init__.py
│   ├── core.py              # Main AnalysisAgent class: orchestrates parsing, frame extraction, LLM verification, and report generation.
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── helper.py        # MultimodalConversableAgent and utilities for LLM and image handling.
│   │   └── config_manager.py# Singleton config manager; currently hardcoded config for LLM/API.
│   └── tools/
│       ├── __init__.py
│       ├── analyze.py       # Tool function: async wrapper to run deviation analysis via AnalysisAgent.
│       └── registry.py      # Minimal decorator and registry for tool functions.
├── __init__.py
├── main.py                  # CLI entry point: runs AnalysisAgent on provided artifacts.
├── README.md
└── pyproject.toml           # Project metadata and dependencies.
```

## Installation

- Requires **Python 3.8+**

### With [uv](https://github.com/astral-sh/uv) (recommended)

```bash
uv venv .venv
source .venv/bin/activate
uv pip install .
```

## Development Setup

To install dev dependencies and pre-commit hooks:

```bash
uv pip install .[dev]
pre-commit install
```

## Configuration

> **Note:** Configuration is currently hardcoded in `agent/llm/config_manager.py`. To change the OpenAI API key, model, or base URL, edit this file directly. Environment variables are only used if you modify the code to enable them.

- `OPENAI_API_KEY` (required)
- `OPENAI_MODEL` (default: `gpt-4o`)
- `OPENAI_BASE_URL` (default: `https://api.openai.com/v1`)

Example (if you enable environment variable support):

```bash
export OPENAI_API_KEY=sk-...yourkey...
export OPENAI_MODEL=gpt-4o
```

## Usage

### As a Python Library

```python
from agent.core import AnalysisAgent
import asyncio

async def main():
    agent = AnalysisAgent()
    report = await agent.analyze('path/to/agent_inner_thoughts.json', 'path/to/test.feature_result.html')
    print(report)

asyncio.run(main())
```

### Command-Line Interface (CLI)

```bash
python main.py --planning_log path/to/agent_inner_thoughts.json --final_output path/to/test.feature_result.html
```

Deviation report will be printed and saved as `deviation_report.json` in the output directory.

---

- This package is **standalone** and does not depend on any external codebase.
- For advanced use, expand the config logic or add CLI wrappers as needed.
