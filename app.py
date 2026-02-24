import os
from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# Initialize Groq Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Request model
class QueryRequest(BaseModel):
    question: str

@app.get("/")
def home():
    return {"message": "🌾 KrishiSahay AI is Running"}

@app.post("/ask")
def ask_question(query: QueryRequest):
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",  # Fast and good for Q&A
            messages=[
                {
                    "role": "system",
                    "content": "You are KrishiSahay, an AI assistant helping farmers with crops, pests, fertilizers, and government schemes."
                },
                {
                    "role": "user",
                    "content": query.question
                }
            ],
            temperature=0.5
        )

        answer = response.choices[0].message.content

        return {
            "question": query.question,
            "answer": answer
        }

    except Exception as e:
        return {"error": str(e)}