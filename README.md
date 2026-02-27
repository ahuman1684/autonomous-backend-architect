# autonomous-backend-architect
An agentic system that generates complete structured backends using LangGraph.

## Overview

This project uses [Groq](https://groq.com) for free LLM inference (no OpenAI key required).
The default model is `llama-3.3-70b-versatile`, which is available for free on Groq and supports tool calling.

## Setup

1. Copy `.env.example` to `.env` and fill in your keys:
   ```
   GROQ_API_KEY=gsk_your_groq_api_key_here
   ```
   Get a free API key at <https://console.groq.com>.

2. Optionally set a different model via the `LLM_MODEL` env var:
   ```
   LLM_MODEL=llama-3.3-70b-versatile  # default
   # LLM_MODEL=llama-3.1-8b-instant
   # LLM_MODEL=mixtral-8x7b-32768
   # LLM_MODEL=gemma2-9b-it
   ```

3. Install dependencies:
   ```
   pip install -e ".[all]"
   ```

4. Run the Streamlit UI:
   ```
   architect-ui
   ```
   Or run from the command line:
   ```
   architect
   ```
