"""
AI Generation Routes
Handles AI-powered LFA generation using HuggingFace models
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import json
import os
from huggingface_hub import InferenceClient

router = APIRouter()

from database import get_database

# ==================== AI CLIENT SETUP ====================

# Use Qwen 2.5 7B - best balance of speed and quality
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

def get_ai_client():
    """Get HuggingFace Inference Client"""
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN not found in environment variables")
    return InferenceClient(token=hf_token)

# ==================== REQUEST/RESPONSE MODELS ====================

class GenerateLFARequest(BaseModel):
    prompt: str = Field(..., description="Detailed description of the program goal")
    organization_id: str
    created_by: str
    theme_id: Optional[str] = None
    target_grades: List[str] = Field(default=[])

# ==================== AI GENERATION FUNCTIONS ====================

async def generate_lfa_with_ai(prompt: str, theme_id: Optional[str] = None) -> dict:
    """
    Use HuggingFace AI to generate LFA structure
    """
    try:
        client = get_ai_client()
        db = get_database()
        
        # Get theme context if provided
        theme_context = ""
        if theme_id:
            theme = db.themes.find_one({"_id": ObjectId(theme_id)})
            if theme:
                theme_context = f"\n\nTheme: {theme['name']}\nDescription: {theme['description']}"
        
        system_prompt = f"""You are an expert educational program designer specializing in Logical Framework Approach (LFA).

Your task is to generate a structured LFA based on the user's program description.

Guidelines:
1. Create a clear, specific challenge statement
2. Generate 2-4 measurable impacts (what change we want to see)
3. Generate 3-6 stakeholder outcomes (what different stakeholders will achieve)
4. Each impact and outcome should have 2-3 specific indicators with baseline, target, and measurement method

Categories for impacts: "Student Learning", "Teacher Capacity", "School Infrastructure", "Community Engagement"
Common stakeholders: "Students", "Teachers", "Principals", "Parents", "Community Members"

Respond ONLY with valid JSON in this exact format:
{{
  "lfa_name": "string (descriptive program name)",
  "challenge_statement": "string (clear problem being solved)",
  "impacts": [
    {{
      "impact_statement": "string",
      "category": "string",
      "indicators": [
        {{
          "indicator_text": "string",
          "baseline_value": "string",
          "target_value": "string",
          "measurement_method": "string"
        }}
      ]
    }}
  ],
  "outcomes": [
    {{
      "outcome_statement": "string",
      "stakeholder_type": "string",
      "indicators": [
        {{
          "indicator_text": "string",
          "baseline_value": "string",
          "target_value": "string",
          "measurement_method": "string"
        }}
      ]
    }}
  ]
}}

Do not include any markdown formatting, explanations, or text outside the JSON object.{theme_context}"""

        user_message = f"Create a detailed LFA for the following program:\n\n{prompt}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Call HuggingFace API
        response = client.chat_completion(
            model=MODEL_ID,
            messages=messages,
            max_tokens=2000,
            temperature=0.7
        )
        
        # Extract response
        response_text = response.choices[0].message.content.strip()
        
        # Clean JSON if wrapped in markdown
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        generated_lfa = json.loads(response_text)
        
        return generated_lfa
        
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI generated invalid JSON: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

# ==================== ROUTES ====================

@router.post("/generate-lfa")
async def generate_lfa(request: GenerateLFARequest):
    """
    Generate LFA draft using AI
    """
    db = get_database()
    
    try:
        # Verify organization and user exist
        org = db.organizations.find_one({"_id": ObjectId(request.organization_id)})
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        user = db.users.find_one({"_id": ObjectId(request.created_by)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate LFA using AI
        print(f"Generating LFA for prompt: {request.prompt[:100]}...")
        generated_data = await generate_lfa_with_ai(request.prompt, request.theme_id)
        
        # Store impacts in database and get IDs
        impact_refs = []
        for impact_data in generated_data["impacts"]:
            impact_doc = {
                "impact_statement": impact_data["impact_statement"],
                "category": impact_data["category"],
                "indicators": impact_data["indicators"],
                "theme_id": request.theme_id,
                "is_template": False,
                "created_by": request.created_by,
                "created_at": datetime.utcnow()
            }
            result = db.impacts.insert_one(impact_doc)
            
            impact_refs.append({
                "impact_id": str(result.inserted_id),
                "impact_statement": impact_data["impact_statement"],
                "custom_indicators": []
            })
        
        # Store outcomes in database and get IDs
        outcome_refs = []
        for outcome_data in generated_data["outcomes"]:
            outcome_doc = {
                "outcome_statement": outcome_data["outcome_statement"],
                "stakeholder_type": outcome_data["stakeholder_type"],
                "indicators": outcome_data["indicators"],
                "is_template": False,
                "created_by": request.created_by,
                "created_at": datetime.utcnow()
            }
            result = db.outcomes.insert_one(outcome_doc)
            
            outcome_refs.append({
                "outcome_id": str(result.inserted_id),
                "outcome_statement": outcome_data["outcome_statement"],
                "stakeholder_type": outcome_data["stakeholder_type"],
                "custom_indicators": []
            })
        
        # Create LFA document
        lfa_data = {
            "name": generated_data["lfa_name"],
            "organization_id": request.organization_id,
            "created_by": request.created_by,
            "target_grades": request.target_grades,
            "theme_id": request.theme_id,
            "challenge_statement": generated_data["challenge_statement"],
            "challenge_context": None,
            "impacts": impact_refs,
            "outcomes": outcome_refs,
            "status": "draft",
            "collaborators": [],
            "version": 1,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "approved_at": None,
            "execution_started_at": None
        }
        
        result = db.lfas.insert_one(lfa_data)
        lfa_data["_id"] = result.inserted_id
        
        # Update organization LFA count
        db.organizations.update_one(
            {"_id": ObjectId(request.organization_id)},
            {"$inc": {"total_lfas": 1}}
        )
        
        return {
            "message": "LFA generated successfully using AI",
            "lfa_id": str(lfa_data["_id"]),
            "lfa_name": generated_data["lfa_name"],
            "impacts_count": len(impact_refs),
            "outcomes_count": len(outcome_refs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suggest-impacts")
async def suggest_impacts(challenge_statement: str, category: Optional[str] = None):
    """
    Suggest impact statements based on challenge
    """
    try:
        client = get_ai_client()
        
        category_filter = f" in the category '{category}'" if category else ""
        
        prompt = f"""Generate 3-5 measurable impact statements{category_filter} for this educational challenge:

Challenge: {challenge_statement}

Respond with ONLY a JSON array of impacts:
[
  {{
    "impact_statement": "string",
    "category": "string",
    "indicators": [
      {{
        "indicator_text": "string",
        "baseline_value": "string",
        "target_value": "string",
        "measurement_method": "string"
      }}
    ]
  }}
]"""

        messages = [{"role": "user", "content": prompt}]
        
        response = client.chat_completion(
            model=MODEL_ID,
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Clean JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        suggested_impacts = json.loads(response_text)
        
        return {
            "suggested_impacts": suggested_impacts,
            "count": len(suggested_impacts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI suggestion failed: {str(e)}")

@router.post("/suggest-outcomes")
async def suggest_outcomes(
    challenge_statement: str,
    stakeholder_type: Optional[str] = None
):
    """
    Suggest outcome statements for stakeholders
    """
    try:
        client = get_ai_client()
        
        stakeholder_filter = f" for '{stakeholder_type}'" if stakeholder_type else ""
        
        prompt = f"""Generate 3-5 measurable outcome statements{stakeholder_filter} for this educational challenge:

Challenge: {challenge_statement}

Common stakeholders: Students, Teachers, Principals, Parents, Community Members

Respond with ONLY a JSON array of outcomes:
[
  {{
    "outcome_statement": "string",
    "stakeholder_type": "string",
    "indicators": [
      {{
        "indicator_text": "string",
        "baseline_value": "string",
        "target_value": "string",
        "measurement_method": "string"
      }}
    ]
  }}
]"""

        messages = [{"role": "user", "content": prompt}]
        
        response = client.chat_completion(
            model=MODEL_ID,
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Clean JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        suggested_outcomes = json.loads(response_text)
        
        return {
            "suggested_outcomes": suggested_outcomes,
            "count": len(suggested_outcomes)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI suggestion failed: {str(e)}")

@router.get("/health")
async def ai_health_check():
    """Check if AI service is available"""
    try:
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            return {
                "status": "unhealthy",
                "error": "HF_TOKEN not configured"
            }
        
        return {
            "status": "healthy",
            "model": MODEL_ID,
            "token_configured": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }