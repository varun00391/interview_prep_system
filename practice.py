"""
create a simple function which takes resume in pdf file as input 
and then generate questions for different rounds based on the 
resume using llm.
"""


import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import httpx
import fitz 
from dotenv import load_dotenv

# load .env file to environment
load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Load API key from environment
# GROQ_API_KEY = GROQ_API_KEY
if not GROQ_API_KEY:
    raise RuntimeError("Please set the GROQ_API_KEY environment variable")

# Load system prompt from file
with open("prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# Groq API endpoint
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

app = FastAPI(
    title="Resume Question Generator",
    description="Generates interview questions from a provided resume using Groq API",
    version="1.0.0"
)

class Question(BaseModel):
    question: str
    notes: str | None = None

class QuestionsResponse(BaseModel):
    round_1: list[Question]
    round_2: list[Question]
    round_3: list[Question]
    round_4: list[Question]


def extract_text_from_pdf(file: UploadFile) -> str:
    try:
        with fitz.open(stream=file.file.read(), filetype="pdf") as doc:
            text = "\n".join([page.get_text() for page in doc])
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {e}")


@app.post("/generate-questions", response_model=QuestionsResponse)
async def generate_questions_from_pdf(file: UploadFile = File(...)):
    resume_text = extract_text_from_pdf(file)

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-oss-120b",  # Change to your desired Groq model
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": resume_text}
        ],
        # "max_tokens": 800,
        "temperature": 0.7
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(GROQ_ENDPOINT, json=payload, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Groq API error: {response.text}")

    data = response.json()
    try:
        result = data["choices"][0]["message"]["content"]
        # questions_json = httpx._models.jsonlib.loads(result)
        import json
        import re

        try:
            json_str = re.search(r"\{.*\}", result, re.S).group()  # extract JSON block
            questions_json = json.loads(json_str)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Invalid JSON in Groq response: {e}\nRaw output: {result}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse Groq response: {e}")

    return QuestionsResponse(**questions_json)
