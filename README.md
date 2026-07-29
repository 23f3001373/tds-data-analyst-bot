# Data Analyst Telegram Bot (TDS Project 1)

An autonomous LLM agent built for Telegram that receives data analysis questions, processes inline data / public statistics (e.g. MOSPI), and replies with exact structured JSON output.

## Features
- **Strict JSON Response Format**: Always returns `{"answer": <result_in_requested_shape>, "log_url": "https://your-host/run.jsonl"}`.
- **Multi-turn Context**: Tracks conversation history per chat and answers the latest query in context.
- **Public Log Hosting**: Includes a built-in FastAPI log server to serve `run.jsonl` publicly for evaluation grading.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```bash
   export TELEGRAM_BOT_TOKEN="<your_telegram_bot_token>"
   export GEMINI_API_KEY="<your_gemini_api_key>"
   export LOG_BASE_URL="<your_public_domain_or_ngrok_url>"
   ```

3. Run log server:
   ```bash
   python log_server.py
   ```

4. Run Telegram bot:
   ```bash
   python bot.py
   ```
