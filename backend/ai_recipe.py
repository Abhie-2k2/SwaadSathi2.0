import os
import re
import json
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.0-pro")

if not GEMINI_API_KEY:
    raise Exception("Gemini API key not found in .env file.")

genai.configure(api_key=GEMINI_API_KEY)

router = APIRouter(tags=["AI Recipes"])

# ---------- Request Models ----------
class RecipeRequest(BaseModel):
    ingredients: str
    preferences: str = ""

class PromptRequest(BaseModel):
    prompt: str

# ---------- Helper ----------
def parse_recipe_text(text: str):
    json_match = re.search(r"```json(.*?)```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    title = ""
    ingredients = []
    instructions = []

    title_match = re.search(r"Recipe Title:\s*(.+)", text)
    if title_match:
        title = title_match.group(1).strip()

    ingredients_match = re.search(r"Ingredients:\s*((?:- .+\n?)*)", text)
    if ingredients_match:
        ingredients_text = ingredients_match.group(1)
        ingredients = [line.strip("- ").strip() for line in ingredients_text.splitlines() if line.strip()]

    instructions_match = re.search(r"Instructions:\s*((?:\d+\..+\n?)*)", text)
    if instructions_match:
        instructions_text = instructions_match.group(1)
        instructions = [line.split(".", 1)[1].strip() for line in instructions_text.splitlines() if "." in line]

    if not title and not ingredients and not instructions:
        return {"raw_text": text}

    return {
        "title": title or "Untitled Recipe",
        "ingredients": ingredients,
        "instructions": instructions
    }

# ---------- Endpoint 1: Structured Recipe ----------
@router.post("/recipe_suggestion")
async def ai_recipe_suggestion(data: RecipeRequest):
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        prompt = f"""
Suggest a recipe based on the following ingredients: {data.ingredients}.
Consider dietary preferences: {data.preferences}.

Return the response in this JSON format inside a ```json ... ``` code block:

{{
  "title": "Recipe Title",
  "ingredients": ["ingredient 1", "ingredient 2"],
  "instructions": ["Step 1", "Step 2"]
}}

If JSON isn't possible, output using these labeled sections:

Recipe Title: ...
Ingredients:
- item
- item
Instructions:
1. step
2. step
"""
        response = model.generate_content(prompt)
        content = getattr(response, "text", None)

        if not content:
            raise HTTPException(status_code=500, detail="No response text from Gemini.")

        parsed = parse_recipe_text(content)
        return {"recipe": parsed}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini SDK error: {str(e)}")

# ---------- Endpoint 2: Freeform Chat ----------
@router.post("/chat")
async def ai_chat(data: PromptRequest):
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(data.prompt)
        return {"response": getattr(response, "text", "No reply from Gemini.")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini Chat error: {str(e)}")
