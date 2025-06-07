from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
from firebase_admin import auth, firestore
import firebase_admin
import os

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    from firebase_admin import credentials
    cred_path = os.getenv(
        "FIREBASE_ADMIN_CRED",
        r"C:\Users\Abhijeet\Documents\GitHub\SwaadSathi\swaadsathi-2025-firebase-adminsdk-fbsvc-c20d63f0df.json"
    )
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

# Firestore client
db = firestore.client()

# API router
router = APIRouter(prefix="/profile", tags=["User Profile"])

# ========================
# === Pydantic Models ===
# ========================

class UserProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    dietary_preferences: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None

# ==============================
# === Auth Dependency Utils ===
# ==============================

async def get_current_user_id(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing authorization token")
    id_token = authorization.split("Bearer ")[1]
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token["uid"]
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")

# =========================
# === Profile Endpoints ===
# =========================

@router.get("/")
async def get_profile(uid: str = Depends(get_current_user_id)):
    try:
        user_ref = db.collection("user_profiles").document(uid)
        doc = user_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Profile not found")
        return {"profile": doc.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching profile: {str(e)}")

@router.put("/")
async def update_profile(data: UserProfile, uid: str = Depends(get_current_user_id)):
    try:
        update_data = data.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No data provided for update")

        user_ref = db.collection("user_profiles").document(uid)
        user_ref.set(update_data, merge=True)
        return {"message": "Profile updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")
