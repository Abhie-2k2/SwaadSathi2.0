from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Request, Query, Path, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import List
from pymongo import MongoClient
from bson import ObjectId
import os
import shutil
from datetime import datetime
from auth import get_current_user_id
from dotenv import load_dotenv
import uuid
from pydantic import BaseModel

load_dotenv()

router = APIRouter()

# Connect to MongoDB
client = MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017/"))
db = client["swaadsathi"]
recipes_collection = db["recipes"]
comments_collection = db["comments"]  # Comments collection

# Directory to store uploaded images
UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Utility function to save uploaded image with unique filename
def save_uploaded_image(image: UploadFile) -> str:
    ext = os.path.splitext(image.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    image_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    return f"/uploaded_images/{unique_filename}"

# -------------------- Recipe APIs --------------------

# Add a new recipe
@router.post("/add_recipe", status_code=status.HTTP_201_CREATED)
async def add_recipe(
    request: Request,
    title: str = Form(...),
    ingredients: str = Form(...),
    steps: str = Form(...),
    category: str = Form(...),
    image: UploadFile = File(None),
    user_id: str = Depends(get_current_user_id)
):
    image_url = None
    if image:
        try:
            image_url = save_uploaded_image(image)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image save failed: {str(e)}")

    recipe = {
        "title": title,
        "ingredients": ingredients,
        "steps": steps,
        "category": category,
        "image_url": image_url,
        "user_id": user_id,
        "created_at": datetime.utcnow()
    }

    result = recipes_collection.insert_one(recipe)
    return JSONResponse(status_code=201, content={"message": "Recipe added", "id": str(result.inserted_id)})


# Get all recipes with pagination and sorting
@router.get("/get_recipes")
async def get_all_recipes(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc")
):
    sort_direction = 1 if sort_order == "asc" else -1
    allowed_sort_fields = {"title", "category", "user_id", "created_at"}
    if sort_by not in allowed_sort_fields:
        sort_by = "created_at"

    total = recipes_collection.count_documents({})
    cursor = recipes_collection.find().sort(sort_by, sort_direction).skip(skip).limit(limit)
    recipes = list(cursor)
    for recipe in recipes:
        recipe["id"] = str(recipe["_id"])
        del recipe["_id"]

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "recipes": recipes
    }


# Get single recipe by ID, optionally with comments
@router.get("/get_recipe/{recipe_id}")
async def get_recipe(recipe_id: str, include_comments: bool = Query(False)):
    recipe = recipes_collection.find_one({"_id": ObjectId(recipe_id)})
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    recipe["id"] = str(recipe["_id"])
    del recipe["_id"]

    if include_comments:
        comments_cursor = comments_collection.find({"recipe_id": ObjectId(recipe_id)}).sort("timestamp", -1)
        recipe["comments"] = [
            {
                "id": str(c["_id"]),
                "user_id": c["user_id"],
                "comment_text": c["comment_text"],
                "timestamp": c["timestamp"].isoformat()
            } for c in comments_cursor
        ]
    return recipe


# Get recipes created by logged-in user
@router.get("/get_my_recipes")
async def get_my_recipes(user_id: str = Depends(get_current_user_id)):
    recipes = list(recipes_collection.find({"user_id": user_id}))
    for recipe in recipes:
        recipe["id"] = str(recipe["_id"])
        del recipe["_id"]
    return recipes


# Update a recipe by recipe_id
@router.put("/update_recipe/{recipe_id}")
async def update_recipe(
    recipe_id: str = Path(...),
    title: str = Form(None),
    ingredients: str = Form(None),
    steps: str = Form(None),
    category: str = Form(None),
    image: UploadFile = File(None),
    user_id: str = Depends(get_current_user_id)
):
    recipe = recipes_collection.find_one({"_id": ObjectId(recipe_id)})

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    if recipe["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this recipe")

    update_data = {}

    if title:
        update_data["title"] = title
    if ingredients:
        update_data["ingredients"] = ingredients
    if steps:
        update_data["steps"] = steps
    if category:
        update_data["category"] = category

    if image:
        try:
            update_data["image_url"] = save_uploaded_image(image)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image save failed: {str(e)}")

    if update_data:
        recipes_collection.update_one({"_id": ObjectId(recipe_id)}, {"$set": update_data})

    return {"message": "Recipe updated successfully"}


# Delete a recipe by recipe_id
@router.delete("/delete_recipe/{recipe_id}")
async def delete_recipe(
    recipe_id: str,
    user_id: str = Depends(get_current_user_id)
):
    recipe = recipes_collection.find_one({"_id": ObjectId(recipe_id)})

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    if recipe["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this recipe")

    recipes_collection.delete_one({"_id": ObjectId(recipe_id)})

    return {"message": "Recipe deleted successfully"}


# Search recipes by keyword and/or category
@router.get("/search_recipes")
async def search_recipes(
    keyword: str = Query(None, description="Keyword to search in recipe titles"),
    category: str = Query(None, description="Category to filter recipes"),
):
    query = {}
    if keyword:
        query["title"] = {"$regex": keyword, "$options": "i"}  # case-insensitive regex match
    if category:
        query["category"] = category

    recipes = list(recipes_collection.find(query))
    for recipe in recipes:
        recipe["id"] = str(recipe["_id"])
        del recipe["_id"]
    return recipes


# -------------------- Comments Feature --------------------

class Comment(BaseModel):
    recipe_id: str
    comment_text: str

# Add a comment to a recipe
@router.post("/add_comment")
async def add_comment(comment: Comment, user_id: str = Depends(get_current_user_id)):
    # Check if recipe exists
    recipe = recipes_collection.find_one({"_id": ObjectId(comment.recipe_id)})
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    comment_doc = {
        "recipe_id": ObjectId(comment.recipe_id),
        "user_id": user_id,
        "comment_text": comment.comment_text,
        "timestamp": datetime.utcnow()
    }

    comments_collection.insert_one(comment_doc)
    return {"message": "Comment added successfully"}


# Get all comments for a recipe, newest first
@router.get("/get_comments/{recipe_id}")
async def get_comments(recipe_id: str):
    comments_cursor = comments_collection.find({"recipe_id": ObjectId(recipe_id)}).sort("timestamp", -1)
    comments = []
    for c in comments_cursor:
        comments.append({
            "id": str(c["_id"]),
            "user_id": c["user_id"],
            "comment_text": c["comment_text"],
            "timestamp": c["timestamp"].isoformat()
        })
    return comments
