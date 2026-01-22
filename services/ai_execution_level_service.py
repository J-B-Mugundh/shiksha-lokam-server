
import os, json
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()
MODEL_ID="meta-llama/Llama-3.3-70B-Instruct"

def get_client():
    return InferenceClient(token=os.getenv("HF_TOKEN"))

async def generate_execution_levels(lfa:dict):
    client=get_client()
    resp=client.chat_completion(
        model=MODEL_ID,
        messages=[
            {"role":"system","content":"Return valid JSON only"},
            {"role":"user","content":str(lfa)}
        ],
        max_tokens=1500
    )
    return json.loads(resp.choices[0].message.content)
