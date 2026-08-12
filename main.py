import os
import json
import logging
import time
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
import threading

# Load .env file if present
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from agent import DataAnalystAgent

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

LOG_FILE = Path(__file__).parent / "logs" / "run.jsonl"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
LOG_BASE_URL = os.environ.get("LOG_BASE_URL", "")

app_fastapi = FastAPI(title="Data Analyst Bot Log Server")

@app_fastapi.get("/")
def read_root():
    return {"status": "ok", "service": "Data Analyst Bot Log Server", "log_endpoint": "/run.jsonl"}

@app_fastapi.get("/run.jsonl")
def get_run_logs():
    if not LOG_FILE.exists():
        LOG_FILE.touch()
    return FileResponse(path=LOG_FILE, filename="run.jsonl", media_type="application/x-ndjson")

chat_histories = {}
agent = DataAnalystAgent()

def record_log(chat_id: int, user_input: str, answer: dict, log_url: str):
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

    answer = agent.solve(chat_histories[chat_id])
    
    # Resolve log_url dynamically if LOG_BASE_URL is not set
    current_log_url = LOG_BASE_URL
    if not current_log_url:
        current_log_url = "http://localhost:8000"
    
    log_url = f"{current_log_url.rstrip('/')}/run.jsonl"

    record_log(chat_id, user_text, answer, log_url)

    response_payload = {
        "answer": answer,
        "log_url": log_url
    }

    chat_histories[chat_id].append({"role": "assistant", "content": json.dumps(response_payload)})
    await update.message.reply_text(json.dumps(response_payload))

def run_fastapi():
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app_fastapi, host="0.0.0.0", port=port)

def main():
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN is missing.")
        return

    # Start FastAPI server in a background thread
    t = threading.Thread(target=run_fastapi, daemon=True)
    t.start()

    app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start_command))
    app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print(f"Bot & Server online and running (Token: {BOT_TOKEN[:10]}...)...")
    app_telegram.run_polling()

if __name__ == "__main__":
    main()
