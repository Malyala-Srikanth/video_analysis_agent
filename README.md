# Analysis Agent (Standalone)

This folder contains a **standalone analysis agent** for visual verification of test steps using multimodal LLMs (e.g., GPT-4o). It is fully independent from the main `testzeus_hercules` codebase.

## What is this?

- The `AnalysisAgent` is designed to:
  - Parse planned test steps and test result HTML.
  - Extract frames from a video proof.
  - Use a multimodal LLM to verify if each step is visually observed in the video.
  - Output a deviation report for each step.

## Folder Structure

```
analysis_agent/
├── agent.py              # Main AnalysisAgent class
├── tool.py               # Tool function for deviation analysis
├── llm_helper.py         # Minimal LLM helper utilities (standalone)
├── llm_config_manager.py # Minimal config manager (standalone, hardcoded config)
├── tool_registry.py      # Minimal tool decorator (standalone)
├── __init__.py           # Package marker
└── README.md             # This file
```

## Usage

1. **Install dependencies:**

   - Requires Python 3.8+
   - Install the following packages:
     - `autogen`
     - `opencv-python`
     - `pillow`
     - `beautifulsoup4`

   Example:

   ```bash
   pip install autogen opencv-python pillow beautifulsoup4
   ```
2. **Configure the agent:**

   - The model and API key are set in `llm_config_manager.py` (edit as needed for your environment).
3. **Example usage:**

   ```python
   from analysis_agent.agent import AnalysisAgent
   import asyncio

   async def main():
       agent = AnalysisAgent()
       report = await agent.analyze('path/to/agent_inner_thoughts.json', 'path/to/test.feature_result.html')
       print(report)

   asyncio.run(main())
   ```
4. **As a tool:**

   - The `analyze_test_deviation` function in `tool.py` can be used as a callable tool in agent frameworks.

## Notes

- This package is **fully standalone** and does not depend on any code from `testzeus_hercules`.
- To change the LLM or API settings, edit the config in `llm_config_manager.py`.
- For advanced use, you may want to expand the config logic or add CLI wrappers.

---

**Maintainer:** You!
