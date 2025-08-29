# Leadership AI Agent

## Overview
This project is an AI agent that uses Playwright (with CDP) for browser automation and integrates with Gemini (or OpenAI) as the backend LLM model.

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```
2. Configure your Gemini or OpenAI API keys as needed.

## Usage
- The agent can automate browser tasks and extract information using LLMs.

## Structure
- `app/` - Main application code
- `requirements.txt` - Python dependencies

## Notes
- Ensure Chrome/Chromium is available for Playwright with CDP support.
