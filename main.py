from fastapi import FastAPI, HTTPException
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import os
from pathlib import Path

# Load environment variables
load_dotenv()

# Set HuggingFace cache to project directory
PROJECT_DIR = Path(__file__).parent.absolute()
CACHE_DIR = os.path.join(PROJECT_DIR, ".cache", "huggingface")
os.makedirs(CACHE_DIR, exist_ok=True)
os.environ["HF_HOME"] = CACHE_DIR
os.environ["TRANSFORMERS_CACHE"] = CACHE_DIR

mongodb_client = None
db = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB and load model
    global mongodb_client, db
    try:        
        uri = os.getenv("MONGODB_URI")
        mongodb_client = MongoClient(uri, server_api=ServerApi('1'))
        mongodb_client.admin.command('ping')
        print("✓ Successfully connected to MongoDB!")
        
        # Select your database
        db = mongodb_client["shiksha-lokam"]
        
        # Load the HuggingFace model
        load_model()
        
    except Exception as e:
        print(f"✗ Startup failed: {e}")
    
    yield
    
    # Shutdown: Close MongoDB connection
    if mongodb_client:
        mongodb_client.close()
        print("✓ MongoDB connection closed")

# Initialize FastAPI with lifespan
app = FastAPI(lifespan=lifespan, title="Shiksha Lokam API")

# ==================== SCHEMAS ====================

class Milestone(BaseModel):
    milestone_id: Optional[str] = None
    title: str = Field(..., description="Title of the milestone")
    description: str = Field(..., description="Detailed description of what needs to be achieved")
    order: int = Field(..., description="Order/sequence of this milestone")
    estimated_duration: str = Field(..., description="Estimated time to complete (e.g., '2 weeks', '1 month')")
    success_criteria: List[str] = Field(..., description="List of criteria to measure success")
    resources: Optional[List[str]] = Field(default=[], description="Recommended resources or materials")
    is_completed: bool = Field(default=False)
    completed_at: Optional[datetime] = None

class EducationalLevel(BaseModel):
    level_id: Optional[str] = None
    level_name: str = Field(..., description="Name of the educational level (e.g., 'Beginner Python Developer')")
    description: str = Field(..., description="Description of this educational level")
    success_indicator: str = Field(..., description="What success looks like at this level")
    milestones: List[Milestone] = Field(default=[], description="List of milestones for this level")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class LevelGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Detailed prompt describing the educational level and goals")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Create a learning path for becoming a Full Stack Web Developer. Success indicator: Able to build and deploy a complete web application with authentication, database, and API."
            }
        }

# ==================== LLM INTEGRATION ====================

# ==================== HUGGINGFACE MODEL SETUP ====================

from transformers import AutoProcessor, Glm4vForConditionalGeneration
import torch
import json

MODEL_PATH = "zai-org/GLM-4.1V-9B-Thinking"

# Global model variables
processor = None
model = None

def load_model():
    """Load the HuggingFace model (assumes it's already downloaded)"""
    global processor, model
    
    if processor is None or model is None:
        print("Loading GLM-4.1V-9B model from cache...")
        
        try:
            processor = AutoProcessor.from_pretrained(MODEL_PATH, use_fast=True)
            model = Glm4vForConditionalGeneration.from_pretrained(
                pretrained_model_name_or_path=MODEL_PATH,
                torch_dtype=torch.bfloat16,
                device_map="auto",
            )
            print("✓ Model loaded successfully!")
        except Exception as e:
            print(f"✗ Error loading model: {e}")
            print("Please run 'python download_model.py' first to download the model.")
            raise

async def generate_milestones_with_llm(prompt: str, success_indicator: str) -> dict:
    """
    Use HuggingFace GLM-4.1V model to generate educational level and milestones
    """
    try:
        # Ensure model is loaded
        load_model()
        
        system_instruction = """You are an expert educational curriculum designer. Your task is to create detailed learning milestones for educational levels.

Given a learning goal and success indicator, you must:
1. Create a clear educational level name and description
2. Generate 5-8 progressive milestones that lead to the success indicator
3. For each milestone, provide: title, description, order, estimated duration, success criteria, and recommended resources

Respond ONLY with valid JSON in this exact format:
{
  "level_name": "string",
  "description": "string",
  "milestones": [
    {
      "title": "string",
      "description": "string",
      "order": number,
      "estimated_duration": "string",
      "success_criteria": ["string"],
      "resources": ["string"]
    }
  ]
}"""

        user_prompt = f"{system_instruction}\n\nCreate a detailed learning path for the following:\n\nGoal: {prompt}\n\nSuccess Indicator: {success_indicator}\n\nGenerate the educational level and milestones in JSON format."
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_prompt
                    }
                ],
            }
        ]
        
        # Process input
        inputs = processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt"
        ).to(model.device)
        
        # Generate response
        generated_ids = model.generate(**inputs, max_new_tokens=2048)
        output_text = processor.decode(
            generated_ids[0][inputs["input_ids"].shape[1]:], 
            skip_special_tokens=True
        )
        
        print(f"Model output: {output_text}")
        
        # Extract JSON from response
        response_text = output_text.strip()
        
        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        return json.loads(response_text)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(e)}")

# ==================== API ENDPOINTS ====================

@app.get("/")
def read_root():
    return {
        "message": "Shiksha Lokam - Educational Milestone API",
        "endpoints": {
            "generate_level": "POST /api/levels/generate",
            "get_levels": "GET /api/levels",
            "get_level": "GET /api/levels/{level_id}",
            "update_milestone": "PATCH /api/levels/{level_id}/milestones/{milestone_id}"
        }
    }

@app.post("/api/levels/generate", response_model=dict)
async def generate_educational_level(request: LevelGenerationRequest):
    """
    Generate an educational level with milestones using Claude AI
    """
    try:
        # Extract success indicator from prompt or use default
        success_indicator = "Successfully complete all milestones and demonstrate competency"
        
        # Generate milestones using LLM
        llm_response = await generate_milestones_with_llm(request.prompt, success_indicator)
        
        # Create educational level document
        level_data = {
            "level_name": llm_response["level_name"],
            "description": llm_response["description"],
            "success_indicator": success_indicator,
            "milestones": llm_response["milestones"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert into MongoDB
        collection = db["educational_levels"]
        result = collection.insert_one(level_data)
        
        return {
            "level_id": str(result.inserted_id),
            "message": "Educational level created successfully",
            "level_name": llm_response["level_name"],
            "milestones_count": len(llm_response["milestones"])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/levels", response_model=List[dict])
def get_all_levels():
    """
    Get all educational levels
    """
    try:
        collection = db["educational_levels"]
        levels = list(collection.find({}, {"_id": 1, "level_name": 1, "description": 1, "created_at": 1}))
        
        # Convert ObjectId to string
        for level in levels:
            level["level_id"] = str(level.pop("_id"))
        
        return levels
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/levels/{level_id}")
def get_level(level_id: str):
    """
    Get a specific educational level with all milestones
    """
    try:
        from bson import ObjectId
        collection = db["educational_levels"]
        
        level = collection.find_one({"_id": ObjectId(level_id)})
        
        if not level:
            raise HTTPException(status_code=404, detail="Level not found")
        
        level["level_id"] = str(level.pop("_id"))
        return level
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/levels/{level_id}/milestones/{milestone_order}")
def update_milestone_completion(level_id: str, milestone_order: int, completed: bool):
    """
    Mark a milestone as completed or incomplete
    """
    try:
        from bson import ObjectId
        collection = db["educational_levels"]
        
        update_data = {
            f"milestones.{milestone_order - 1}.is_completed": completed,
            "updated_at": datetime.utcnow()
        }
        
        if completed:
            update_data[f"milestones.{milestone_order - 1}.completed_at"] = datetime.utcnow()
        
        result = collection.update_one(
            {"_id": ObjectId(level_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Level not found")
        
        return {"message": "Milestone updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/levels/{level_id}")
def delete_level(level_id: str):
    """
    Delete an educational level
    """
    try:
        from bson import ObjectId
        collection = db["educational_levels"]
        
        result = collection.delete_one({"_id": ObjectId(level_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Level not found")
        
        return {"message": "Level deleted successfully"}
        
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