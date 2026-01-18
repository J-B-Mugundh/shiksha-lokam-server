from fastapi import FastAPI, HTTPException
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional

# MongoDB connection URI
uri = "mongodb+srv://admin:adminmafia@cluster0.twzmx5d.mongodb.net/?appName=Cluster0"

# Load environment variables
load_dotenv()
# Global MongoDB client
import os
mongodb_client = None
db = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB
    global mongodb_client, db
    try:        
        mongodb_client = MongoClient(uri, server_api=ServerApi('1'))
        mongodb_client.admin.command('ping')
        print("✓ Successfully connected to MongoDB!")
        
        # Select your database
        db = mongodb_client["shiksha-lokam"]
        
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
    
    yield
    
    # Shutdown: Close MongoDB connection
    if mongodb_client:
        mongodb_client.close()
        print("✓ MongoDB connection closed")

# Initialize FastAPI with lifespan
app = FastAPI(lifespan=lifespan)

# Example Pydantic model
class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "FastAPI + MongoDB API"}

# Example: Create item
@app.post("/items/", response_model=dict)
def create_item(item: Item):
    try:
        collection = db["items"]
        result = collection.insert_one(item.dict())
        return {"id": str(result.inserted_id), "message": "Item created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Example: Get all items
@app.get("/items/", response_model=List[dict])
def get_items():
    try:
        collection = db["items"]
        items = list(collection.find({}, {"_id": 0}))
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Example: Get item by name
@app.get("/items/{name}")
def get_item(name: str):
    try:
        collection = db["items"]
        item = collection.find_one({"name": name}, {"_id": 0})
        if item:
            return item
        raise HTTPException(status_code=404, detail="Item not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
def health_check():
    try:
        mongodb_client.admin.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}