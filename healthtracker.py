from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from auth import get_current_user  # adjust to your actual auth module
from db import get_db  # adjust to your actual db connection module

router = APIRouter(prefix="/health")

class BMIRecord(BaseModel):
    weight: float
    height: float
    bmi: float
    timestamp: Optional[datetime] = None

    class Config:
        orm_mode = True

@router.post("/bmi")
async def save_bmi(
    record: BMIRecord,
    current_user=Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        record.timestamp = datetime.utcnow()
        data = record.dict()
        data["user_id"] = current_user  # `get_current_user` should return uid string
        await db["bmi_records"].insert_one(data)
        return {"message": "BMI record saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bmi", response_model=List[BMIRecord])
async def get_bmi_records(
    current_user=Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        cursor = db["bmi_records"].find({"user_id": current_user}).sort("timestamp", -1)
        records = await cursor.to_list(length=100)
        return [BMIRecord(**record) for record in records]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
