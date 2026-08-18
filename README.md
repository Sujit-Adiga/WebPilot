# BrowserPilot

LLM-driven browser automation agent using Gemini and Playwright.

## Architecture

User Goal
    ↓
Gemini Planner
    ↓
BrowserAction
    ↓
Action Executor
    ↓
Playwright
    ↓
Browser State Inspection
    ↓
Action History
    ↓
Replanning

## Setup

### 1. Clone

git clone https://github.com/Sujit-Adiga/BrowserPilot.git
cd BrowserPilot

### 2. Install dependencies

pip install -r requirements.txt
playwright install chromium

### 3. Configure API key

Create a `.env` file:

GEMINI_API_KEY=your_api_key

### 4. Run

python main.py
