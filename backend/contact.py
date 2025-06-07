# contact.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from firebase_admin import firestore

router = APIRouter()

db = firestore.client()

class ContactMessage(BaseModel):
    name: str
    email: str
    message: str

@router.post("/contact")
async def submit_contact_form(data: ContactMessage):
    try:
        db.collection("contact_messages").add(data.dict())
        return {"status": "success", "message": "Message submitted successfully"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
