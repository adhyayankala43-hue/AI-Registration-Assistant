"""
Manages the MongoDB connection and handles default data initialization.
"""
import pymongo
import threading
from typing import Dict, Any
from config import MONGO_URI

try:
    mongo_client = pymongo.MongoClient(MONGO_URI)
    mongo_db = mongo_client["university_portal"]
    mongo_collection = mongo_db["system_data"]
    mongo_client.admin.command('ping')
    print("✅ Successfully connected to MongoDB!")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")

FILE_LOCK = threading.Lock()

DEFAULT_DATA = {
    "courses": {
        "CS101": {"title": "Intro to Computer Science", "dept": "CS", "credits": 3, "seats": 5, "days": "Mon/Wed", "start_time": "10:00 AM", "end_time": "11:30 AM"},
        # ... (Include the rest of your DEFAULT_DATA courses here) ...
    },
    "students": {},
    "analytics": {"total_logins": 0, "registrations": 0},
    "chat_logs": []
}

def load_database() -> Dict[str, Any]:
    with FILE_LOCK:
        doc = mongo_collection.find_one({"_id": "main_data"})
        if not doc:
            mongo_collection.insert_one({"_id": "main_data", **DEFAULT_DATA})
            return DEFAULT_DATA
        doc.pop("_id", None)
        if "analytics" not in doc:
            doc["analytics"] = {"total_logins": 0, "registrations": 0}
        if "chat_logs" not in doc:
            doc["chat_logs"] = []
        return doc

def save_database(data: Dict[str, Any]) -> None:
    with FILE_LOCK:
        mongo_collection.update_one(
            {"_id": "main_data"},
            {"$set": data},
            upsert=True
        )
