# ATeam Kids Academy - Phonics Assessment Platform

A kid-friendly phonics assessment platform with AI-powered speech analysis, built with Next.js frontend and FastAPI backend.

## Architecture

```
├── api_server.py          # FastAPI REST API backend
├── pdf_generator.py       # PDF report generation
├── llm.py                 # OpenAI GPT integration
├── prompts.py             # LLM prompt templates
├── get_speech_metrics.py  # SpeechSuper API integration
├── record_and_analyze.py  # Audio analysis pipeline
├── .env                   # Environment variables
├── phonics_questions_age_5_6.json  # Question bank
├── backend_requirements.txt
└── frontend/              # Next.js frontend
    ├── app/
    │   ├── page.tsx           # Landing page
    │   ├── assessment/page.tsx # Assessment setup
    │   ├── quiz/page.tsx      # Quiz flow
    │   └── results/page.tsx   # Results dashboard
    ├── components/            # Reusable UI components
    └── lib/api.ts             # API client
```

## Quick Start

### 1. Start the Backend API

```bash
cd "Initial Assessment"
pip install -r backend_requirements.txt
python api_server.py
```

The API server will run on **http://localhost:8000**

### 2. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will run on **http://localhost:3000**

### 3. Open the App

Navigate to **http://localhost:3000** in your browser.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/questions/generate` | Generate quiz questions |
| POST | `/api/tts/generate` | Generate text-to-speech audio |
| POST | `/api/tts/question` | Generate TTS for a specific question |
| POST | `/api/audio/upload` | Upload recorded audio |
| POST | `/api/audio/analyze` | Analyze pronunciation |
| POST | `/api/quiz/submit` | Submit quiz and get feedback |
| GET | `/api/metrics/{username}` | Get user metrics |
| POST | `/api/report/generate` | Generate PDF report |

## Environment Variables

Create a `.env` file in the root directory:

```
ACADEMY_NAME="ATeam Kids Academy"
OPENAI_API_KEY="your-openai-api-key"
```
