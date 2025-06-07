from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Connect to MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["swaadsathi"]

# Default users collection
users_collection = db["users"]

def save_user_to_db(user_data):
    """
    Insert a new user or update existing user by uid.
    """
    filter_ = {"uid": user_data["uid"]}
    update_ = {"$set": user_data}  # Replace existing fields or add new ones
    result = users_collection.update_one(filter_, update_, upsert=True)
    if result.upserted_id:
        return f"Inserted new user with id {result.upserted_id}"
    elif result.modified_count > 0:
        return "Updated existing user"
    else:
        return "No changes made"

def get_collection(name):
    """
    Return a MongoDB collection by name.
    """
    return db[name]
