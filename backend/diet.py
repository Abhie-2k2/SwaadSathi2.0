from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from firebase_admin import auth as firebase_auth

router = APIRouter(prefix="/diet", tags=["Diet"])

class DietRequest(BaseModel):
    age: int
    gender: str  # "male" or "female"
    weight_kg: float
    height_cm: float
    activity_level: str  # "low", "moderate", "high"

def verify_token(token: str):
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def get_token_from_header(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split("Bearer ")[1]
    return verify_token(token)

@router.post("/get-diet-plan")
async def get_diet_plan(request: DietRequest, user=Depends(get_token_from_header)):
    try:
        if request.gender.lower() == "male":
            bmr = 10 * request.weight_kg + 6.25 * request.height_cm - 5 * request.age + 5
        else:
            bmr = 10 * request.weight_kg + 6.25 * request.height_cm - 5 * request.age - 161

        activity_factor = {
            "low": 1.2,
            "moderate": 1.55,
            "high": 1.9
        }.get(request.activity_level.lower(), 1.2)

        tdee = bmr * activity_factor

        protein = round(0.8 * request.weight_kg, 1)
        carbs = round((0.5 * tdee) / 4, 1)
        fats = round((0.25 * tdee) / 9, 1)

        activities = {
            "low": ["15-minute stretching", "light yoga"],
            "moderate": ["30-minute walk", "beginner home workout"],
            "high": ["45-minute workout", "intermediate yoga", "cycling"]
        }

        return {
            "daily_calories": round(tdee, 2),
            "protein_g": protein,
            "carbohydrates_g": carbs,
            "fats_g": fats,
            "activity_suggestions": activities.get(request.activity_level.lower(), [])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diet calculation failed: {str(e)}")
