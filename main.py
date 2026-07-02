import os
import json
import base64
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
from prompts import SYSTEM_PROMPT, ANALYSIS_SCHEMA_PROMPT, build_reply_prompt

load_dotenv()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

app = FastAPI(title="Smart Reply AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in prod to your app's scheme/domain
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_NAME = "gemini-3.5-flash"
model = genai.GenerativeModel(MODEL_NAME, system_instruction=SYSTEM_PROMPT)


class AnalysisResponse(BaseModel):
    relationship: str
    mood: str
    intent: str
    language_style: str
    last_message_summary: str
    conversation_subject: str = "self"
    third_party_context: str = ""


class ReplyRequest(BaseModel):
    analysis: dict
    goal: str
    memory: dict | None = None
    person_name: str = ""
    relationship: str = ""

@app.post("/generate-replies")
async def generate_replies(payload: ReplyRequest):
    prompt = build_reply_prompt(
        payload.goal,
        payload.analysis,
        payload.memory,
        payload.person_name,
        payload.relationship,
    )
    try:
        result = model.generate_content(prompt)
        parsed = _extract_json(result.text)
        return parsed
    except Exception as e:
        raise HTTPException(502, f"Gemini reply generation failed: {e}")


def _extract_json(raw_text: str) -> dict:
    cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)



class ScreenshotRequest(BaseModel):
    image_base64: str
    mime_type: str = "image/jpeg"

@app.post("/process-screenshot", response_model=AnalysisResponse)
async def process_screenshot(payload: ScreenshotRequest):
    import base64
    image_bytes = base64.b64decode(payload.image_base64)
    if not image_bytes:
        raise HTTPException(400, "Empty image")
    prompt_parts = [
        ANALYSIS_SCHEMA_PROMPT,
        {"mime_type": payload.mime_type, "data": image_bytes},
    ]
    try:
        result = model.generate_content(prompt_parts)
        parsed = _extract_json(result.text)
        return AnalysisResponse(**parsed)
    except Exception as e:
        raise HTTPException(502, f"Gemini analysis failed: {e}")

@app.get("/health")
async def health():
    return {"status": "ok"}
