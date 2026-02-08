# Hackathon Encode — Multi-Agent Nutrition Assistant

A working multi-agent workflow built with LangGraph and LLM agents to analyze user journal entries, detect eating triggers, and suggest healthy meals with logistics (scheduling/grocery). This application demonstrates preference learning, trigger detection, nutrition suggestion, and logistics agents wired together in a StateGraph.

## Features
- **Preference learning agent**: Extracts and updates user food preferences using JSON parsing
- **Trigger detective**: Analyzes journal entries for emotional/environmental triggers with structured output
- **Nutritionist agent**: Recommends specific meals based on profile, health data, and triggers
- **Logistics agent**: Generates grocery lists and scheduling plans automatically
- **Safety Guardrails**: Protects against prompt injections and harmful nutritional advice

## Prerequisites
- Python 3.10+
- A Groq API key (or OpenAI API key if you switch providers)

## Installation

### 1. Clone the repo
```bash
git clone https://github.com/nvipin63/hackathon_encode.git
cd hackathon_encode
```

### 2. Create and activate a virtual environment (recommended)
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

If you encounter issues with pip, try:
```bash
python -m pip install -r requirements.txt
```

### 4. Set up your environment variables
Create a `.env` file in the root directory:
```bash
cp .env.example .env
```

Then edit `.env` and add your API key. By default, the app uses **Groq** via the `ChatGroq` class:
```
GROQ_API_KEY=your-actual-api-key-here
# OR if using OpenAI directly (requires code change, see below)
# OPENAI_API_KEY=your-openai-api-key
```

## LLM Configuration

Currently, the project uses **ChatGroq** with the `openai/gpt-oss-120b` model for fast and efficient inference.

### Switching LLM Providers
You can easily switch to OpenAI or other providers by modifying `main.py`:

**To use OpenAI (GPT-4 / GPT-3.5):**
1. Install the OpenAI package: `pip install langchain-openai`
2. Update `main.py`:
```python
# Comment out ChatGroq import
# from langchain_groq import ChatGroq

# Uncomment ChatOpenAI import
from langchain_openai import ChatOpenAI

# Update initialization
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0
)
```

## Usage

### Web Interface (Recommended)
1. Start the Flask web server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. Enter your journal entry, select your preferences, and click "Analyze My Journal"

4. Watch as the AI agents process your input and provide personalized recommendations!

### Command Line Interface
For the original CLI experience, run:
```bash
python main.py
```

The script runs a scenario simulating a journal entry with stress and low energy, demonstrating the complete workflow through all four agents.

## What's New
This version includes significant improvements over the original hackathon demo:

✅ **Safety Guardrails** to prevent harmful output and prompt injections
✅ **Fixed critical syntax error** preventing the script from running
✅ **Structured JSON parsing** for all agent outputs
✅ **Proper error handling** with fallback mechanisms
✅ **Working preference agent** that actually updates user profiles
✅ **Enhanced trigger detection** with reliable structured output
✅ **Detailed nutritionist recommendations** with specific meals and reasoning
✅ **Intelligent logistics** that extracts ingredients and creates formatted plans
✅ **Environment validation** to ensure API key is configured

## Extending the Project
- Add more trigger types or health metrics
- Integrate real calendar/shopping APIs (Google Calendar, Instacart)
- Add a web interface or chatbot frontend
- Implement user authentication and persistent storage
- Create more complex routing logic with parallel agent execution

## Troubleshooting

**ModuleNotFoundError**: Make sure you've installed dependencies with `pip install -r requirements.txt`

**API Key Error**: Ensure your `.env` file exists and contains a valid API key.

**Python/Pip not found**: Ensure Python 3.10+ is installed and added to your system PATH

## Deployment

### Vercel
This project is configured for easy deployment on [Vercel](https://vercel.com).

1. Install the Vercel CLI (optional) or connect your GitHub repository to Vercel.
2. If using the CLI:
   ```bash
   vercel
   ```
3. Set your environment variables in the Vercel dashboard:
   - `GROQ_API_KEY`: Your Groq API key

### Troubleshooting Vercel 500 Errors
If you see a "500: INTERNAL_SERVER_ERROR" or "FUNCTION_INVOCATION_FAILED":
1. Check Vercel Logs: Go to the Vercel dashboard > Deployments > [Your Deployment] > Functions to see the error traceback.
2. Verify API Keys: Ensure `GROQ_API_KEY` (or `OPENAI_API_KEY`) is set in Vercel Settings > Environment Variables.
3. Check Dependencies: Ensure `requirements.txt` includes all necessary packages.

The `vercel.json` and `api/index.py` files are already configured to serve the Flask application as a Serverless Function.

## License
Apache License 2.0

## Disclaimer
This application uses Artificial Intelligence to generate text and nutritional recommendations. The content produced by this app is for informational purposes only and should not be considered medical advice. AI models can hallucinate or produce inaccurate information. Always proceed with caution and consult with a qualified healthcare professional before making significant changes to your diet or health routine.
