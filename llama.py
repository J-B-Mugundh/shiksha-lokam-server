import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

MODEL_ID = "meta-llama/Llama-3.2-3B-Instruct"  # ✅ Llama 3.2 (3B) - Good balance
# MODEL_ID = "meta-llama/Llama-3.2-1B-Instruct"  # ✅ Llama 3.2 (1B) - Faster, smaller
# MODEL_ID = "HuggingFaceH4/zephyr-7b-beta"  # ✅ Zephyr 7B - Good chat model
# MODEL_ID = "microsoft/Phi-3.5-mini-instruct"  # ✅ Phi-3.5 - Microsoft's model
# MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"  # ✅ Qwen 2.5 - Very fast
# MODEL_ID = "Qwen/Qwen2.5-3B-Instruct"  # ✅ Qwen 2.5 - Larger version

def get_client():
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN not found in environment variables")
    
    return InferenceClient(token=hf_token)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    system_message: str = "You are a helpful AI assistant."
    chat_history: list[ChatMessage] = []
    user_text: str

@app.get("/")
def read_root():
    return {
        "message": "HuggingFace Free Serverless API",
        "model": MODEL_ID,
        "note": "Using HuggingFace free tier - Serverless Inference API"
    }

@app.post("/chat")
def chat(req: ChatRequest):
    try:
        client = get_client()

        # Build messages
        messages = [
            {"role": "system", "content": req.system_message}
        ]
        
        # Add chat history
        for msg in req.chat_history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": req.user_text
        })

        # Call HuggingFace Free Serverless API
        response = client.chat_completion(
            model=MODEL_ID,
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )

        # Extract response
        assistant_message = response.choices[0].message.content

        return {"response": assistant_message.strip()}

    except Exception as e:
        # Better error handling
        error_message = str(e)
        if "410" in error_message or "deprecated" in error_message.lower():
            raise HTTPException(
                status_code=500, 
                detail=f"Model {MODEL_ID} is no longer supported. Please update MODEL_ID to a supported model."
            )
        raise HTTPException(status_code=500, detail=f"Error: {error_message}")

@app.get("/health")
def health_check():
    try:
        hf_token = os.getenv("HF_TOKEN")
        if hf_token:
            return {
                "status": "healthy",
                "model": MODEL_ID,
                "token": "configured"
            }
        else:
            return {"status": "unhealthy", "error": "HF_TOKEN not found"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}