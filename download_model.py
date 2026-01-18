"""
Script to download and cache a lightweight model
Run this once before starting the FastAPI server
"""

import os
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Set cache directory to current project directory
PROJECT_DIR = Path(__file__).parent.absolute()
CACHE_DIR = os.path.join(PROJECT_DIR, ".cache", "huggingface")
os.makedirs(CACHE_DIR, exist_ok=True)
os.environ["HF_HOME"] = CACHE_DIR
os.environ["TRANSFORMERS_CACHE"] = CACHE_DIR

# Using a much smaller model (~1GB)
MODEL_PATH = "Qwen/Qwen2.5-0.5B-Instruct""""
Script to download and cache the GLM-4.1V-9B model
Run this once before starting the FastAPI server
"""

import os
from pathlib import Path
from transformers import AutoProcessor, Glm4vForConditionalGeneration
import torch

# Set cache directory to current project directory
PROJECT_DIR = Path(__file__).parent.absolute()
CACHE_DIR = os.path.join(PROJECT_DIR, ".cache", "huggingface")
TEMP_DIR = os.path.join(PROJECT_DIR, ".temp")

# Create directories
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Set environment variables for cache AND temp
os.environ["HF_HOME"] = CACHE_DIR
os.environ["TRANSFORMERS_CACHE"] = CACHE_DIR
os.environ["TEMP"] = TEMP_DIR
os.environ["TMP"] = TEMP_DIR
os.environ["TMPDIR"] = TEMP_DIR

MODEL_PATH = "zai-org/GLM-4.1V-9B-Thinking"

def download_model():
    print("=" * 60)
    print("Downloading GLM-4.1V-9B-Thinking Model")
    print("=" * 60)
    print(f"Model: {MODEL_PATH}")
    print(f"Cache Directory: {CACHE_DIR}")
    print(f"Temp Directory: {TEMP_DIR}")
    print("This is a one-time download (~18GB)")
    print("=" * 60)
    
    try:
        # Download processor
        print("\n[1/2] Downloading processor...")
        processor = AutoProcessor.from_pretrained(MODEL_PATH, use_fast=True)
        print("✓ Processor downloaded successfully!")
        
        # Download model
        print("\n[2/2] Downloading model (this will take a while)...")
        model = Glm4vForConditionalGeneration.from_pretrained(
            pretrained_model_name_or_path=MODEL_PATH,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        print("✓ Model downloaded successfully!")
        
        print("\n" + "=" * 60)
        print("✓ ALL DONE! Model is cached and ready to use.")
        print("You can now run: uvicorn main:app --reload")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error downloading model: {e}")
        print("Please check your internet connection and try again.")

if __name__ == "__main__":
    download_model()