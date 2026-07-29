import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="Data Analyst Bot Log Server")

LOG_FILE = Path(__file__).parent / "logs" / "run.jsonl"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Data Analyst Bot Log Server", "log_endpoint": "/run.jsonl"}

@app.get("/run.jsonl")
def get_run_logs():
    if not LOG_FILE.exists():
        # Create empty log file if not existing
        LOG_FILE.touch()
    return FileResponse(path=LOG_FILE, filename="run.jsonl", media_type="application/x-ndjson")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
