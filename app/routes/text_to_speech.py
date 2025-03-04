from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse
from time import time
from typing import List
import openai
import os
import whisper
import requests

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
    print("text: ", text)
    try:
        messages= [
                {"role": "developer", "content": [{"type": "text", "text": "You are a creative screenwriter that writes description about scenes based on prompts keyword from user.  Limit each scene description to 1000 characters"}]},
                {"role": "user", "content": [{"type": "text", "text": f"Write One short scene descriptions for: {text}"}]}
            ],
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
base_url = "http://localhost:8880/v1/audio"
async def generate_text_to_speech_audio(texts: List[str], voice: str):
    current_time = int(time() * 1000)
    temp_dir = "temp_audios"
    os.makedirs(temp_dir, exist_ok=True)
    audio_files = []
    for index, text in enumerate(texts):
        try:
            # Generate audio for each text
            response = requests.post(
                f"{base_url}/speech",
                json={
                    "model": "kokoro",  
                    "input": text,  # Dynamically change the input text
                    "voice": voice,  # Cycle through voices if there are multiple
                    "response_format": "mp3",  # Can be wav, opus, etc.
                    "speed": 1.0  # Modify speed if necessary
                }
            )
            response.raise_for_status()  # Ensure the request was successful
                
            # Save the generated audio to a file
            speech_file_path = os.path.join(temp_dir, f"{current_time}-{index}-speech.mp3")
            with open(speech_file_path, "wb") as f:
                    f.write(response.content)
            audio_files.append(speech_file_path)
            print(f"Audio for '{text[:30]}...' saved as {speech_file_path}.")
        except requests.exceptions.RequestException as e:
            print(f"Error generating or saving audio for text {index}: {e}")
    return {"data": audio_files}
# async def generate_text_to_speech_audio(texts: List[str]):
#     current_time = int(time() * 1000)
#     temp_dir = "temp_audios"
#     os.makedirs(temp_dir, exist_ok=True)
#     audio_files = []
#     for (index, text) in enumerate(texts):
#         response = openai.audio.speech.create(model=os.getenv("OPENAI_TTS_MODEL"), input=text, voice="alloy")
#         speech_file_path = os.path.join(temp_dir, f"{current_time}-{index}-speech.mp3")
#         response.write_to_file(speech_file_path)
#         audio_files.append(speech_file_path)
#     return { "data": audio_files }

async def generate_timestamp_from_audio(audios: List[str]):
    model = whisper.load_model("base")
    transcriptions = []
    for audio_file in audios:
        if not os.path.exists(audio_file):
            print(f"File not found! {audio_file}")
            raise FileNotFoundError(f"The file {audio_file} does not exist.")
        result = model.transcribe(audio_file, word_timestamps=True)
        transcription = { "file": audio_file, "text": result["text"], "segments": result["segments"] }
        transcriptions.append(transcription)
    return { "data": transcriptions }
