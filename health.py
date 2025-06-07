from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from firebase_admin import auth, firestore
from typing import Optional
import firebase_admin
import os

# Initialize Firebase Admin app (if not done already)
if not firebase_admin._apps:
    from firebase_admin import credentials
    cred_path = os.getenv(
        "FIREBASE_ADMIN_CRED",
        r"C:\Users\Abhijeet\Documents\GitHub\SwaadSathi\swaadsathi-2025-firebase-adminsdk-fbsvc-c20d63f0df.json"
    )
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()
router = APIRouter()

# Pydantic model for POST input
class BMIData(BaseModel):
    weight: float
    height: float
    bmi: float

# Extract UID from token
async def get_current_user_id(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing authorization token")
    id_token = authorization.split("Bearer ")[1]
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token["uid"]
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")

# Save BMI data
@router.post("/health/bmi")
async def submit_bmi(data: BMIData, uid: str = Depends(get_current_user_id)):
    try:
        user_ref = db.collection("user_profiles").document(uid)
        user_ref.set({
            "bmi_data": {
                "weight": data.weight,
                "height": data.height,
                "bmi": data.bmi
            }
        }, merge=True)
        return {"message": "BMI data saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Retrieve BMI data
@router.get("/health/bmi")
async def get_bmi(uid: str = Depends(get_current_user_id)):
    try:
        user_ref = db.collection("user_profiles").document(uid)
        doc = user_ref.get()
        if doc.exists:
            bmi_data = doc.to_dict().get("bmi_data")
            if bmi_data:
                return {"bmi_data": bmi_data}
            else:
                raise HTTPException(status_code=404, detail="BMI data not found")
        else:
            raise HTTPException(status_code=404, detail="User profile not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/health/exercise-suggestion")
async def exercise_suggestion(uid: str = Depends(get_current_user_id)):
    try:
        user_ref = db.collection("user_profiles").document(uid)
        doc = user_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User profile not found")

        bmi_data = doc.to_dict().get("bmi_data")
        if not bmi_data or "bmi" not in bmi_data:
            raise HTTPException(status_code=404, detail="BMI data not found")

        bmi = bmi_data["bmi"]

        # Simple exercise suggestions based on BMI ranges
        if bmi < 18.5:
            suggestion = [
                "Light yoga stretches",
                "Walking for 30 minutes",
                "Strength training with light weights"
            ]
        elif 18.5 <= bmi < 25:
            suggestion = [
                "Cardio exercises (running, cycling)",
                "Power yoga",
                "Strength training"
            ]
        elif 25 <= bmi < 30:
            suggestion = [
                "Low-impact cardio (swimming, brisk walking)",
                "Yoga for weight loss",
                "Strength training with moderate weights"
            ]
        else:  # bmi >= 30
            suggestion = [
                "Low-impact exercises (water aerobics, cycling)",
                "Gentle yoga",
                "Consult a fitness expert for personalized plan"
            ]

        return {
            "bmi": bmi,
            "exercise_suggestions": suggestion
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
