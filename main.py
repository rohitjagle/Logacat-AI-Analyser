from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

log_store = {"content": "", "filename": ""}
LOG_TEMP_FILE = os.path.join(tempfile.gettempdir(), "stb_logcat_store.txt")
LOG_META_FILE = os.path.join(tempfile.gettempdir(), "stb_logcat_meta.txt")

def save_log_to_disk(content, filename):
    with open(LOG_TEMP_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    with open(LOG_META_FILE, "w", encoding="utf-8") as f:
        f.write(filename)

def load_log_from_disk():
    try:
        if os.path.exists(LOG_TEMP_FILE) and os.path.exists(LOG_META_FILE):
            with open(LOG_TEMP_FILE, "r", encoding="utf-8") as f:
                content = f.read()
            with open(LOG_META_FILE, "r", encoding="utf-8") as f:
                filename = f.read()
            if content:
                log_store["content"] = content
                log_store["filename"] = filename
    except Exception:
        pass

load_log_from_disk()

SYSTEM_PROMPT = """You are an expert Android QA engineer and log analysis specialist.
You are analyzing a logcat file from an Android STB (Set-Top Box) running an OTT launcher application.
Your job is to help QA engineers quickly identify issues in the logs.

When analyzing logs:
- Highlight ERROR, FATAL, WTF level messages clearly
- Identify API failures (HTTP errors, timeouts, connection issues)
- Spot ANR (Application Not Responding) events
- Find NullPointerExceptions and crashes
- Identify memory issues (OOM, GC pressure)
- Look for CEC/HDMI related errors if asked
- Group related errors together
- Always mention the timestamp and tag of important log lines
- Format your response clearly with sections and bullet points
- If no issues found for the query, say so clearly"""

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/upload")
async def upload_log(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    log_store["content"] = text
    log_store["filename"] = file.filename
    save_log_to_disk(text, file.filename)
    lines = text.strip().split("\n")
    return {
        "status": "success",
        "filename": file.filename,
        "total_lines": len(lines),
        "preview": "\n".join(lines[:10])
    }

@app.post("/ask")
async def ask_question(
    question: str = Form(...),
    provider: str = Form(...),
    api_key: str = Form(...),
    model: str = Form(...)
):
    if not log_store["content"]:
        load_log_from_disk()
    if not log_store["content"]:
        return JSONResponse(status_code=400, content={"error": "No log file uploaded yet."})
    if not api_key.strip():
        return JSONResponse(status_code=400, content={"error": "API key is missing. Please enter your API key in Settings."})

    log_text = log_store["content"]
    MAX_CHARS = 30000
    truncated = log_text[:MAX_CHARS]
    truncation_note = ""
    if len(log_text) > MAX_CHARS:
        truncation_note = "\n[Log truncated to " + str(MAX_CHARS) + " chars. Full size: " + str(len(log_text)) + " chars.]"

    fname = log_store["filename"]
    user_message = "Logcat file: " + fname + "\n\nLog Content:\n" + truncated + truncation_note + "\n\nQA Engineer Question: " + question

    try:
        answer = ""

        if provider == "groq":
            from groq import Groq
            client = Groq(api_key=api_key)
            resp = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                model=model,
                temperature=0.2,
                max_tokens=2048
            )
            answer = resp.choices[0].message.content

        elif provider == "gemini":
            from google import genai
            client = genai.Client(api_key=api_key)
            resp = client.models.generate_content(
                model=model,
                contents=SYSTEM_PROMPT + "\n\n" + user_message
            )
            answer = resp.text

        elif provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                model=model,
                temperature=0.2,
                max_tokens=2048
            )
            answer = resp.choices[0].message.content

        elif provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            resp = client.messages.create(
                model=model,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}]
            )
            answer = resp.content[0].text

        elif provider == "openrouter":
            from openai import OpenAI
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key
            )
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.2,
                max_tokens=2048
            )
            answer = resp.choices[0].message.content

        else:
            return JSONResponse(status_code=400, content={"error": "Unknown provider: " + provider})

        return {"answer": answer}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/log-info")
async def log_info():
    if not log_store["content"]:
        load_log_from_disk()
    if not log_store["content"]:
        return {"loaded": False}
    lines = log_store["content"].split("\n")
    errors = sum(1 for l in lines if " E " in l or "ERROR" in l)
    warnings = sum(1 for l in lines if " W " in l or "WARN" in l)
    fatals = sum(1 for l in lines if " F " in l or "FATAL" in l or " WTF " in l)
    return {
        "loaded": True,
        "filename": log_store["filename"],
        "total_lines": len(lines),
        "errors": errors,
        "warnings": warnings,
        "fatals": fatals
    }
