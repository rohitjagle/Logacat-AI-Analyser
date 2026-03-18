# STB Logcat Analyzer — Gemini AI Powered

## Folder Structure
stb-log-analyzer/
├── main.py
├── index.html
├── requirements.txt
└── README.md

## One-Time Setup

### 1. Open this folder in VS Code
File → Open Folder → select stb-log-analyzer

### 2. Open Terminal in VS Code
Press Ctrl + ` (backtick)

### 3. Create virtual environment
python -m venv venv

### 4. Activate virtual environment
Windows PowerShell:   venv\Scripts\Activate.ps1
Windows CMD:          venv\Scripts\activate.bat

### 5. Install dependencies
pip install -r requirements.txt

---

## Every Time You Want to Use the App

### Step 1 — Open terminal in VS Code and activate venv
venv\Scripts\Activate.ps1

### Step 2 — Set your Gemini API Key
Get free key from: https://aistudio.google.com

PowerShell:   $env:GEMINI_API_KEY="AIzaSy_your_key_here"
CMD:          set GEMINI_API_KEY=AIzaSy_your_key_here

### Step 3 — Run the app
uvicorn main:app --reload --port 8000

### Step 4 — Open browser
Go to: http://localhost:8000

---

## Usage
1. Upload your .txt or .log logcat file
2. View instant stats (errors, warnings, fatals)
3. Click Quick Analysis buttons OR type your own question
4. Gemini AI will analyze and respond

## Example Questions
- Show all API failures and HTTP errors
- Find app crashes and stack traces
- Why is the OTT launcher crashing on startup?
- Show CEC and HDMI related errors
- Summarize the top 5 issues in this log
- Find all NullPointerExceptions
