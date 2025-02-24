from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import example, movie, text_to_speech, generate_ai
import openai
import os

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI(
    title="AI Video Back End Project Python FastAPI",
    description="AI Video Back End Project Python FastAPI",
    version="1.0.0",
)

app.mount("/public", StaticFiles(directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp_videos")), name="public")
app.include_router(example.router)
app.include_router(movie.router)
app.include_router(text_to_speech.router)
app.include_router(generate_ai.router)
