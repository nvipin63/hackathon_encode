# Hackathon Encode — Multi-Agent Nutrition Assistant

A small demo app showing a multi-agent workflow built with LangGraph and LLM agents to analyze user journal entries, detect eating triggers, and suggest healthy meals with logistics (scheduling/grocery). This repository contains a single runnable example in `main.py` that demonstrates preference learning, trigger detection, nutrition suggestion, and logistics agents wired together in a StateGraph.

## Features
- Preference learning agent: extracts and updates user food preferences
- Trigger detective: analyzes journal entries for emotional/environmental triggers
- Nutritionist agent: recommends meals based on profile, health data, and triggers
- Logistics agent: mocks scheduling and grocery list integration

## Prerequisites
- Python 3.10+
- An OpenAI-compatible LLM key set in the environment variable `OPENAI_API_KEY`
- Optional: `python-dotenv` if you prefer loading env vars from a `.env` file

## Install
1. Clone the repo:
   ```bash
   git clone https://github.com/nvipin63/hackathon_encode.git
   cd hackathon_encode
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # macOS / Linux
   .venv\Scripts\activate    # Windows (PowerShell)
   ```
3. Install dependencies (example):
   ```bash
   pip install langchain-openai langchain-core langgraph python-dotenv
   ```

## Usage
- Make sure `OPENAI_API_KEY` is exported in your environment.
- Run the demo:
  ```bash
  python main.py
  ```
- The script runs a scenario that simulates a journal entry with stress and low energy and prints the workflow output.

## Extending the demo
- Replace placeholder parsing with structured function-calling or JSON parsing for robust state updates.
- Add more agents, tools, or connectors (calendar, shopping APIs).
- Improve the router and add more conditional branches or parallel agent runs.

## Notes
- This is a demo and contains simplified/mocked logic for illustration. The LLM responses are invoked directly and some return values are placeholders — plan for robust parsing and error handling before using in production.

## License
- MIT

## Contributing
- Open issues and PRs are welcome.
