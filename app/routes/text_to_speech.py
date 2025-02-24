from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse
from time import time
from typing import List
import openai
import os
import whisper

router = APIRouter(
    prefix="/text-to-speech",
    tags=["Text To Speech"],
)

@router.post("/generate-content")
async def testing_api_key(text: str):
    return await generate_chat_message(text, False)

@router.post("/generate-text-to-speech")
async def movie_combination(texts: List[str]):
    audios = await generate_text_to_speech_audio(texts)
    print(f"Audio Generated: {audios}")
    transcriptions = await generate_timestamp_from_audio(audios.get("data", []))
    print(f"Transcriptions Completed: {transcriptions}")
    return { "audio_files": audios, "transcriptions": transcriptions }

async def generate_chat_message(text: str, code: bool):
    try:
        messages = [{ "role": "user", "content": f"Please Generate Up To 10 Sentences And Maximum 120 Characters Each Sentences {'Split With ++ And Just Value And No Need Number' if code else ''} {'About ' + text if len(text.split()) < 5 else 'Of ' + text}" }]
        response = openai.chat.completions.create(model=os.getenv("OPENAI_MODEL"), messages=messages, max_tokens=300)
        print("API Key Is Working")
        print(f"Response: {response.choices[0].message.content}")
        return { "data": response.choices[0].message.content or "" }
    except openai.AuthenticationError:
        print("Invalid API Key And Please Check Your Key")
        return { "data": "" }
    except Exception as e:
        print(f"An Error Occurred: {e}")
        return { "data": "" }

async def generate_text_to_speech_audio(texts: List[str]):
    current_time = int(time() * 1000)
    temp_dir = "temp_audios"
    os.makedirs(temp_dir, exist_ok=True)
    audio_files = []
    for (index, text) in enumerate(texts):
        response = openai.audio.speech.create(model=os.getenv("OPENAI_TTS_MODEL"), input=text, voice="alloy")
        speech_file_path = os.path.join(temp_dir, f"{current_time}-{index}-speech.mp3")
        response.write_to_file(speech_file_path)
        audio_files.append(speech_file_path)
    return { "data": audio_files }

async def generate_timestamp_from_audio(audios: List[str]):
    model = whisper.load_model("base")
    transcriptions = []
    for audio_file in audios:
        result = model.transcribe(audio_file, word_timestamps=True)
        transcription = { "file": audio_file, "text": result["text"], "segments": result["segments"] }
        transcriptions.append(transcription)
    return { "data": transcriptions }
