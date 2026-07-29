import os
import json
import logging
import time
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
from agent import DataAnalystAgent

# Load .env file if present
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

LOG_FILE = Path(__file__).parent / "logs" / "run.jsonl"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
LOG_BASE_URL = os.environ.get("LOG_BASE_URL", "http://localhost:8000")

# Store conversation history per chat_id
chat_histories = {}
agent = DataAnalystAgent()

def record_log(chat_id: int, user_input: str, answer: dict, log_url: str):
    """Appends a run record to run.jsonl log file."""
    log_entry = {
        "timestamp": time.time(),
        "chat_id": chat_id,
        "input": user_input,
        "answer": answer,
        "log_url": log_url
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Data Analyst Bot is online and ready for queries.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_text = update.message.text

    if chat_id not in chat_histories:
        chat_histories[chat_id] = []

    chat_histories[chat_id].append({"role": "user", "content": user_text})

    # Solve data analysis problem
    answer = agent.solve(chat_histories[chat_id])
    
    log_url = f"{LOG_BASE_URL.rstrip('/')}/run.jsonl"

    # Record log
    record_log(chat_id, user_text, answer, log_url)

    # Required contract: single JSON object with 'answer' and 'log_url'
    response_payload = {
        "answer": answer,
        "log_url": log_url
    }

    # Store assistant answer in history
    chat_histories[chat_id].append({"role": "assistant", "content": json.dumps(response_payload)})

    # Send exact JSON response string
    await update.message.reply_text(json.dumps(response_payload))

def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Error: TELEGRAM_BOT_TOKEN is missing or invalid in environment / .env file.")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print(f"Bot is online and polling for messages (Token: {BOT_TOKEN[:10]}...)...")
    app.run_polling()

if __name__ == "__main__":
    main()
