from fastapi import APIRouter, Request, HTTPException, Header
import firebase_admin
from firebase_admin import credentials, auth, firestore
from pydantic import BaseModel
from typing import List
import os
import asyncio

# Initialize Firebase Admin SDK once
if not firebase_admin._apps:
    cred_path = os.getenv(
        "FIREBASE_ADMIN_CRED",
        r"C:\Users\Abhijeet\Documents\GitHub\SwaadSathi\swaadsathi-2025-firebase-adminsdk-fbsvc-c20d63f0df.json"
    )
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

router = APIRouter()
db = firestore.client()

# Stub async function to save user data to DB (replace with real DB logic)
async def save_user_to_db(user_data: dict):
    # Example: Save user_data in Firestore users collection
    user_ref = db.collection("users").document(user_data["uid"])
    user_ref.set(user_data, merge=True)
    await asyncio.sleep(0)  # simulate async operation

class Preferences(BaseModel):
    uid: str
    diet: str
    allergies: List[str]
    cuisines: List[str]

@router.post("/update-preferences")
async def update_preferences(data: Preferences):
    try:
        user_ref = db.collection("user_profiles").document(data.uid)
        user_ref.set({
            "diet": data.diet,
            "allergies": data.allergies,
            "cuisines": data.cuisines
        }, merge=True)
        return {"message": "Preferences updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/signup")
async def signup(request: Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    try:
        user = auth.create_user(email=email, password=password)
        await save_user_to_db({"uid": user.uid, "email": email})
        return {"message": "User created successfully", "uid": user.uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating user: {str(e)}")

@router.post("/login")
async def login(request: Request):
    body = await request.json()
    id_token = body.get("idToken")
    if not id_token:
        raise HTTPException(status_code=400, detail="Missing ID token")

    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token.get("uid")
        email = decoded_token.get("email", "")
        name = decoded_token.get("name", "")

        if hasattr(request, "session") and request.session is not None:
            request.session["uid"] = uid

        user_data = {
            "uid": uid,
            "email": email,
            "name": name
        }
        await save_user_to_db(user_data)

        return {"message": "Login successful", "uid": uid, "email": email, "name": name}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

@router.get("/verify-session")
async def verify_session(request: Request):
    uid = request.session.get("uid") if (hasattr(request, "session") and request.session is not None) else None
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")
    return {"message": "Session valid", "uid": uid}

@router.post("/logout")
async def logout(request: Request):
    if hasattr(request, "session") and request.session is not None:
        request.session.clear()
    return {"message": "Logged out"}
