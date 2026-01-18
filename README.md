# Shiksha Lokam Server

## Setup Instructions

1. Clone the repository

2. Create a virtual environment:
```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Mac/Linux
```

3. Install dependencies:
```bash
   pip install -r requirements.txt
```

4. Create `.env` file with your MongoDB URI:
```env
   MONGODB_URI=your_mongodb_connection_string
```

5. Download the AI model (one-time, ~18GB): (Not needed right now, we use LLAMA API from HuggingFace for MVP)
```bash
   python download_model.py
```

6. Run the server:
```bash
   uvicorn main:app --reload
```

7. Visit http://127.0.0.1:8000/docs to test the API

## LLAMA HuggingFace API Setup

1. Add Hugging Face API token as follows:
```env
   HF_TOKEN==your_hugging_face_api_key
```

2. Run the server:
```bash
   uvicorn main:app --reload
```

3. Visit http://127.0.0.1:8000/docs to test the LLM API

```json
{
  "system_message": "You are an helpful assistant",
  "chat_history": [
  ],
  "user_text": "Hello"
}
```
