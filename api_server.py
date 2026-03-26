from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List, Literal
from contextlib import asynccontextmanager
import json
import random
import os
import io
import hmac
import hashlib
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import database as phonics_db

import razorpay
import llm
import prompts
import get_speech_metrics
import record_and_analyze
from pronunciation_sound_analysis import analyze_sound_focus

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

# Official frontend only (override with CORS_ORIGINS=comma,separated for local dev)
_CORS_DEFAULT = "https://phonics-assessment.theateamkidsacademy.in"


def _cors_allow_origins() -> List[str]:
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if raw:
        return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]
    return [_CORS_DEFAULT.rstrip("/")]


@asynccontextmanager
async def lifespan(app: FastAPI):
    phonics_db.init_db()
    yield


app = FastAPI(
    title="ATeam Kids Academy - Phonics Assessment API",
    lifespan=lifespan,
)

_CORS_ORIGINS = _cors_allow_origins()
print(f"[phonics-backend] CORS allow_origins: {_CORS_ORIGINS}", flush=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

with open("phonics_questions_age_5_6.json", "r") as f:
    questions_data = json.load(f)


# --- Pydantic Models ---

class QuestionRequest(BaseModel):
    age_group: str
    level: str
    context: str
    session_id: str = ""

class TTSRequest(BaseModel):
    text: str
    voice: str = "shimmer"

class AnalyzeRequest(BaseModel):
    reference_text: str
    child_name: str

class SubmitQuizRequest(BaseModel):
    child_name: str
    age_group: str
    level: str
    questions: list
    user_answers: dict
    pronunciation_metrics: list
    pronunciation_feedbacks: list
    session_id: str = ""

class PDFRequest(BaseModel):
    child_name: str
    age_group: str
    metrics: list
    questions: list
    user_answers: dict
    pronunciation_feedbacks: list
    final_feedback: str
    report_id: Optional[str] = None

class QuestionTTSRequest(BaseModel):
    child_name: str
    question_index: int
    total_questions: int
    question_text: str
    is_pronunciation: bool = False

class CreateOrderRequest(BaseModel):
    purpose: Literal["test_only", "full_bundle", "report_unlock"] = "report_unlock"
    session_id: Optional[str] = None
    report_id: Optional[str] = None

class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    purpose: Literal["test_only", "full_bundle", "report_unlock"] = "report_unlock"
    session_id: Optional[str] = None
    report_id: Optional[str] = None


# --- Razorpay charged amounts (paise only; 100 paise = ₹1) ---
# Change ONLY here. The frontend can show ₹25 / ₹75 / ₹50 for users; this is what Razorpay actually charges.
# Testing: keep 100 each (₹1). Production: e.g. 2500, 7500, 5000.
AMOUNT_TEST_ONLY_PAISE = 100
AMOUNT_FULL_BUNDLE_PAISE = 100
AMOUNT_REPORT_UNLOCK_PAISE = 100


# --- Payments Storage Helpers ---

def _load_payments() -> dict:
    return _normalize_payment_store(phonics_db.load_payment_store())


def _save_payments(data: dict):
    phonics_db.save_payment_store(_normalize_payment_store(data))


def _normalize_payment_store(raw: dict) -> dict:
    if not raw:
        return {"sessions": {}, "reports": {}}
    if "sessions" in raw and "reports" in raw:
        return {
            "sessions": dict(raw.get("sessions") or {}),
            "reports": dict(raw.get("reports") or {}),
        }
    reports = {}
    for k, v in raw.items():
        if isinstance(v, dict) and ("paid" in v or "order_id" in v or "payment_id" in v):
            reports[k] = {
                "report_paid": bool(v.get("paid")),
                "payment_id": v.get("payment_id"),
                "order_id": v.get("order_id"),
            }
    return {"sessions": {}, "reports": reports}


def _session_allows_test(store: dict, session_id: str) -> bool:
    if not session_id or not session_id.strip():
        return False
    s = store["sessions"].get(session_id.strip(), {})
    return bool(s.get("test_paid"))

def _generate_report_id(child_name: str) -> str:
    now = datetime.now()
    ts = now.strftime("%Y%m%d_%H%M%S") + f"{now.microsecond // 1000:03d}"
    safe_name = "".join(c for c in child_name if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
    return f"{ts}_{safe_name}"


# --- Question Generation Logic ---

def get_random_questions(age_group, level, context):
    age_group_data = questions_data.get(age_group, {})
    if not isinstance(age_group_data, dict):
        raise ValueError(f"No data for age group '{age_group}'")

    selected_questions = []
    is_level_1_or_2 = level in ["Level 1", "Level 2"]

    if age_group not in ["9-10", "11-13"]:
        uc_lc_data = age_group_data.get("uppercase_lowercase", [])
        uc_lc_count = 3 if is_level_1_or_2 else 2
        selected_uc_lc = random.sample(uc_lc_data, min(uc_lc_count, len(uc_lc_data)))
        for q in selected_uc_lc:
            q_copy = q.copy()
            q_copy["options"] = ["Upper-Case", "Lower-Case", "Don't Know"]
            if "upper" in q["answer"].lower():
                q_copy["answer"] = "Upper-Case"
            elif "lower" in q["answer"].lower():
                q_copy["answer"] = "Lower-Case"
            else:
                q_copy["answer"] = "Lower-Case"
            selected_questions.append(q_copy)

    should_exclude_syllables = is_level_1_or_2 and age_group in ["3-4", "5-6", "7-8"]
    if not should_exclude_syllables:
        syllable_data = age_group_data.get("syllables", [])
        syllable_count = 2 if age_group not in ["9-10", "11-13"] else 3
        selected_syllables = random.sample(syllable_data, min(syllable_count, len(syllable_data)))
        for q in selected_syllables:
            q_copy = q.copy()
            correct = int(q_copy["answer"])
            options = list(range(1, 6))
            if correct not in options:
                options.append(correct)
            random.shuffle(options)
            q_copy["options"] = [str(opt) for opt in options]
            q_copy["options"].append("Don't Know")
            q_copy["answer"] = str(correct)
            selected_questions.append(q_copy)

    rhyming_data = age_group_data.get("rhyming_words", [])
    if age_group in ["9-10", "11-13"]:
        rhyming_count = 3
    elif should_exclude_syllables:
        rhyming_count = 3
    else:
        rhyming_count = 2
    selected_rhyming = random.sample(rhyming_data, min(rhyming_count, len(rhyming_data)))
    selected_questions.extend(selected_rhyming)

    sentences = []
    for _ in range(4):
        sentence = llm.get_response_from_ai(prompts.generate_text(sentences, context), age_group)
        sentences.append(sentence)

    for sentence in sentences:
        selected_questions.append({
            "question": f"Read the below Sentence: \n{sentence}",
            "answer": sentence,
            "options": []
        })

    return selected_questions


def get_tts_text(child_name, question_index, total_questions, question_text, is_pronunciation=False):
    question_number = question_index + 1
    sanitized_name = child_name.strip() or "there"

    prompts_map = {
        1: f"Hey {sanitized_name}!! let's begin with the first question!",
        3: f"Wow this is awesome {sanitized_name}!!! Let's move on to question {question_number}!",
        5: f"You are half way there! This is great!! Let's move on to question {question_number}!",
        6: f"This looks fantastic {sanitized_name}!! Let's move on to question {question_number}!",
        7: f"Here comes the pronunciation round! Let's move on to question {question_number}!",
        8: f"Great, you are Amazing!!!! Let's move on to question {question_number}!",
        9: f"We are almost done. Let's move on to question {question_number}!",
    }

    if question_number == total_questions:
        prompt = f"Here comes the final question {sanitized_name}! Let's make it count!"
    else:
        prompt = prompts_map.get(question_number, f"Great job! Let's move on to question {question_number}!")

    if is_pronunciation:
        tts_text = f"{prompt} ... Read this sentence."
    else:
        try:
            first, second = question_text.split('\n', 1)
            tts_text = f"{prompt} ... {first} ... {second}"
        except ValueError:
            tts_text = f"{prompt} ... {question_text}"

    return tts_text


# --- API Routes ---

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "name": "ATeam Kids Academy API"}


@app.post("/api/questions/generate")
async def generate_questions(request: QuestionRequest):
    try:
        store = _normalize_payment_store(_load_payments())
        if not _session_allows_test(store, request.session_id or ""):
            raise HTTPException(
                status_code=402,
                detail="Payment required. Complete test access payment before starting the assessment.",
            )
        questions = get_random_questions(request.age_group, request.level, request.context)
        return {"questions": questions}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tts/generate")
async def generate_tts(request: TTSRequest):
    import requests as req
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        json_data = {
            "model": "tts-1",
            "input": request.text,
            "voice": request.voice
        }
        response = req.post("https://api.openai.com/v1/audio/speech", headers=headers, json=json_data)
        if response.status_code == 200:
            return Response(content=response.content, media_type="audio/mpeg")
        else:
            raise HTTPException(status_code=500, detail="TTS generation failed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tts/question")
async def generate_question_tts(request: QuestionTTSRequest):
    import requests as req
    try:
        tts_text = get_tts_text(
            request.child_name,
            request.question_index,
            request.total_questions,
            request.question_text,
            request.is_pronunciation
        )

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        json_data = {"model": "tts-1", "input": tts_text, "voice": "shimmer"}
        response = req.post("https://api.openai.com/v1/audio/speech", headers=headers, json=json_data)
        if response.status_code == 200:
            return Response(content=response.content, media_type="audio/mpeg")
        else:
            raise HTTPException(status_code=500, detail="TTS generation failed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/audio/upload")
async def upload_audio(file: UploadFile = File(...)):
    try:
        os.makedirs("AudioFiles", exist_ok=True)
        output_path = "AudioFiles/output.wav"

        temp_path = f"AudioFiles/temp_{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        from pydub import AudioSegment
        audio = AudioSegment.from_file(temp_path)
        audio = audio.set_channels(1).set_frame_rate(44100)
        audio.export(output_path, format="wav", parameters=["-acodec", "pcm_s16le"])

        if os.path.exists(temp_path):
            os.remove(temp_path)

        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/audio/analyze")
async def analyze_audio(request: AnalyzeRequest):
    try:
        metrics, feedback = record_and_analyze.analyze_recording(
            request.reference_text, request.child_name, model="sent.eval.promax"
        )
        if metrics is not None:
            return {"metrics": metrics, "feedback": feedback}
        else:
            raise HTTPException(status_code=500, detail="Analysis returned None - likely JSON decode error from LLM response")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/quiz/submit")
async def submit_quiz(request: SubmitQuizRequest):
    try:
        store = _normalize_payment_store(_load_payments())
        if not _session_allows_test(store, request.session_id or ""):
            raise HTTPException(
                status_code=402,
                detail="Payment required. Complete test access before submitting the assessment.",
            )

        if len(request.pronunciation_metrics) == 4:
            record_and_analyze.save_user_metrics(request.child_name, request.pronunciation_metrics)

        sound_focus = analyze_sound_focus(request.pronunciation_metrics)

        feedback = ""
        for i, q in enumerate(request.questions):
            if q.get("options"):
                user_answer = request.user_answers.get(f"answer_{i}", "")
                correct = str(q["answer"])
                is_correct = str(user_answer).lower() == correct.lower()
                status = "Correct" if is_correct else "Incorrect"
                feedback += f"{q['question']}. Answer: {user_answer}. Result: {status}\n"
            else:
                user_answer = request.user_answers.get(f"answer_{i}", "")
                feedback += str(user_answer) + "\n"

        final_feedback = llm.get_response_from_ai(
            prompts.get_final_feedback(request.child_name),
            feedback
        )

        import pandas as pd
        records = []
        for i, q in enumerate(request.questions):
            if q.get("options"):
                user_answer = request.user_answers.get(f"answer_{i}", "")
                correct = str(q["answer"])
                is_correct = str(user_answer).lower() == correct.lower()
                records.append({
                    "Child Name": request.child_name,
                    "Question": q["question"],
                    "Options": ", ".join(q["options"]) if q["options"] else "",
                    "Correct Answer": correct,
                    "User Answer": user_answer,
                    "Result": "Correct" if is_correct else "Incorrect"
                })

        if records:
            df = pd.DataFrame(records)
            output_path = "phonics_quiz_results.xlsx"
            if os.path.exists(output_path):
                existing_df = pd.read_excel(output_path)
                df = pd.concat([existing_df, df], ignore_index=True)
            df.to_excel(output_path, index=False)

        report_id = _generate_report_id(request.child_name)

        avg_overall = 0.0
        if request.pronunciation_metrics:
            avg_overall = sum(m.get("overall", 0) for m in request.pronunciation_metrics) / len(request.pronunciation_metrics)

        report_data = {
            "report_id": report_id,
            "child_name": request.child_name,
            "age_group": request.age_group,
            "level": request.level,
            "questions": request.questions,
            "user_answers": request.user_answers,
            "pronunciation_metrics": request.pronunciation_metrics,
            "pronunciation_feedbacks": request.pronunciation_feedbacks,
            "final_feedback": final_feedback,
            "overall_score": round(avg_overall, 1),
            "sound_focus": sound_focus,
            "session_id": (request.session_id or "").strip(),
            "timestamp": datetime.now().isoformat(),
        }
        report_json_path = os.path.join(REPORTS_DIR, f"{report_id}.json")
        with open(report_json_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        try:
            from pdf_generator import generate_pdf_report
            pdf_bytes = generate_pdf_report(
                request.child_name,
                request.age_group,
                request.pronunciation_metrics,
                request.questions,
                request.user_answers,
                request.pronunciation_feedbacks,
                final_feedback,
                sound_focus=sound_focus,
            )
            report_pdf_path = os.path.join(REPORTS_DIR, f"{report_id}.pdf")
            with open(report_pdf_path, "wb") as f:
                f.write(pdf_bytes)
        except Exception:
            import traceback
            traceback.print_exc()

        sid = (request.session_id or "").strip()
        if sid:
            sess = store["sessions"].get(sid, {})
            if sess.get("test_paid") and sess.get("plan") == "full_bundle":
                store["reports"][report_id] = {
                    **store["reports"].get(report_id, {}),
                    "bundle_included": True,
                    "report_paid": True,
                }
                _save_payments(store)

        return {
            "final_feedback": final_feedback,
            "report_id": report_id,
            "overall_score": round(avg_overall, 1),
            "sound_focus": sound_focus,
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics/{username}")
async def get_metrics(username: str):
    try:
        with open("user_metrics.json", "r") as f:
            data = json.load(f)
        if username in data:
            return {"metrics": data[username]}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="No metrics data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/report/generate")
async def generate_report(request: PDFRequest):
    try:
        from pdf_generator import generate_pdf_report
        sf = analyze_sound_focus(request.metrics)
        pdf_bytes = generate_pdf_report(
            request.child_name,
            request.age_group,
            request.metrics,
            request.questions,
            request.user_answers,
            request.pronunciation_feedbacks,
            request.final_feedback,
            sound_focus=sf,
        )

        if hasattr(request, "report_id") and request.report_id:
            report_pdf_path = os.path.join(REPORTS_DIR, f"{request.report_id}.pdf")
            with open(report_pdf_path, "wb") as f:
                f.write(pdf_bytes)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=phonics_report.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Payment Endpoints ---

@app.post("/api/payment/create-order")
async def create_payment_order(request: CreateOrderRequest):
    try:
        if request.purpose in ("test_only", "full_bundle"):
            sid = (request.session_id or "").strip()
            if not sid:
                raise HTTPException(status_code=400, detail="session_id is required for test payments")
            amount = AMOUNT_TEST_ONLY_PAISE if request.purpose == "test_only" else AMOUNT_FULL_BUNDLE_PAISE
            receipt = sid.replace("-", "")[:40] or "sess"
            notes = {"purpose": request.purpose, "session_id": sid}
        elif request.purpose == "report_unlock":
            rid = (request.report_id or "").strip()
            if not rid:
                raise HTTPException(status_code=400, detail="report_id is required for report unlock")
            amount = AMOUNT_REPORT_UNLOCK_PAISE
            receipt = rid[:40]
            notes = {"purpose": "report_unlock", "report_id": rid}
        else:
            raise HTTPException(status_code=400, detail="Invalid payment purpose")

        order_data = {
            "amount": amount,
            "currency": "INR",
            "receipt": receipt,
            "notes": notes,
        }
        order = razorpay_client.order.create(data=order_data)

        store = _normalize_payment_store(_load_payments())
        if request.purpose in ("test_only", "full_bundle"):
            sid = (request.session_id or "").strip()
            prev = store["sessions"].get(sid, {})
            store["sessions"][sid] = {
                **prev,
                "pending_order_id": order["id"],
                "pending_plan": request.purpose,
                "pending_at": datetime.now().isoformat(),
            }
        else:
            rid = (request.report_id or "").strip()
            prev = store["reports"].get(rid, {})
            store["reports"][rid] = {
                **prev,
                "pending_order_id": order["id"],
                "pending_at": datetime.now().isoformat(),
            }
        _save_payments(store)

        return {
            "order_id": order["id"],
            "key_id": RAZORPAY_KEY_ID,
            "amount": amount,
            "currency": "INR",
            "purpose": request.purpose,
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/payment/verify")
async def verify_payment(request: VerifyPaymentRequest):
    try:
        msg = request.razorpay_order_id + "|" + request.razorpay_payment_id
        generated_signature = hmac.new(
            RAZORPAY_KEY_SECRET.encode("utf-8"),
            msg.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if generated_signature != request.razorpay_signature:
            raise HTTPException(status_code=400, detail="Invalid payment signature")

        store = _normalize_payment_store(_load_payments())
        now = datetime.now().isoformat()

        if request.purpose in ("test_only", "full_bundle"):
            sid = (request.session_id or "").strip()
            if not sid:
                raise HTTPException(status_code=400, detail="session_id is required")
            prev = store["sessions"].get(sid, {})
            store["sessions"][sid] = {
                **prev,
                "test_paid": True,
                "plan": request.purpose,
                "payment_id": request.razorpay_payment_id,
                "order_id": request.razorpay_order_id,
                "verified_at": now,
            }
            store["sessions"][sid].pop("pending_order_id", None)
            store["sessions"][sid].pop("pending_plan", None)
        else:
            rid = (request.report_id or "").strip()
            if not rid:
                raise HTTPException(status_code=400, detail="report_id is required")
            prev = store["reports"].get(rid, {})
            store["reports"][rid] = {
                **prev,
                "report_paid": True,
                "payment_id": request.razorpay_payment_id,
                "order_id": request.razorpay_order_id,
                "verified_at": now,
            }
            store["reports"][rid].pop("pending_order_id", None)

        _save_payments(store)

        return {"verified": True, "plan": request.purpose if request.purpose != "report_unlock" else None}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/payment/session-status/{session_id}")
async def get_session_payment_status(session_id: str):
    store = _normalize_payment_store(_load_payments())
    s = store["sessions"].get(session_id.strip(), {})
    return {
        "test_paid": bool(s.get("test_paid")),
        "plan": s.get("plan"),
    }


@app.get("/api/payment/status/{report_id}")
async def get_payment_status(report_id: str):
    store = _normalize_payment_store(_load_payments())
    entry = store["reports"].get(report_id, {})
    paid = bool(entry.get("report_paid") or entry.get("bundle_included"))
    return {"paid": paid, "payment_id": entry.get("payment_id")}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
