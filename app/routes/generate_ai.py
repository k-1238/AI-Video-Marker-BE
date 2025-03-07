from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import FileResponse
from moviepy import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip, ImageClip, AudioFileClip, vfx
from sklearn.feature_extraction.text import TfidfVectorizer
import random
from time import time
from typing import List
from collections import Counter
from . import text_to_speech, generate_video, movie
import os
import json
import re
import requests
import logging
from requests.exceptions import RequestException, HTTPError, Timeout
import openai

router = APIRouter(prefix="/api/generate-ai", tags=["Generate AI"])
openai.api_key = os.getenv("OPENAI_API_KEY")
# Set up logging for better error traceability
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_pixabay_image(query, each_text_scene, job_id_key):
    """Fetches an image URL from Pixabay based on the given query."""
    fetched_url = []
    sentences = each_text_scene.split(". ")
    len_sentence = len(sentences)
    
    url = f"https://pixabay.com/api/?key={os.getenv('PIXABAY_API_KEY')}&q={query['data']}"
    current_time = int(time() * 1000)
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "hits" in data and len(data["hits"]) > 0:
            hits = data["hits"]

            # Ensure we have enough images for the number of sentences
            images_to_use = hits[:len_sentence]  # Limit images to the number of sentences
            if len(images_to_use) == 0:
                raise HTTPException(status_code=404, detail="No images found for the query")
            if len(images_to_use) < len(sentences):
                raise HTTPException(status_code=404, detail="The image length must be the same with sentence length.!!!")

            # Iterate through sentences and pick one image for each sentence
            for i, img in enumerate(images_to_use):
                if i < len(images_to_use):  # Only process if there's an image for the sentence
                    image_url = img.get("webformatURL")
                    if image_url:
                        image_path = f"temp_images/{current_time}-{job_id_key}-Sentence-{i + 1}.png"
                        os.makedirs(os.path.dirname(image_path), exist_ok=True)

                        # Handling image download with retries and timeout
                        try:
                            img_response = requests.get(image_url, timeout=10)
                            img_response.raise_for_status()  # Check for successful response
                            with open(image_path, "wb") as f:
                                f.write(img_response.content)

                            # Success log after image is saved
                            print(f"Image for sentence {i+1} successfully generated and saved at {image_path}")
                            fetched_url.append(image_path)

                        except (RequestException, HTTPError, Timeout) as e:
                            logger.error(f"Failed to download image: {e}")
                            raise HTTPException(status_code=500, detail=f"Failed to download image: {str(e)}")

        return fetched_url  # Return the list of fetched URLs

async def process_scenes(each_text_scene, job_id_key):
    """Processes each scene, extracting sentences, generating image descriptions, and fetching images."""
    query = await generate_video.acceded_character(each_text_scene)
    fetched_img_urls = await get_pixabay_image(query, each_text_scene, job_id_key)
    os.makedirs(os.path.dirname("temp_images/"), exist_ok=True)
    return fetched_img_urls

@router.post("")
async def generate_ai(request: Request, type: str = Form("image"), voice: str=Form(""), prompt_text: str = Form(""), array_text: str = Form(""), duration_total: int = Form(...), duration_per_scene: int = Form(...), orientation: str = Form(...), font_size: int = Form(...), font_color: str = Form(...), transition: str = Form(...)):
    """
    prompt_text => Text Prompt
    duration => Video Duration In Second
    orientation => Orientation Between Landscape Or Portrait
    """
    max_response_limit = 0
    if (duration_per_scene <= 10):
        max_response_limit = 80
    elif (duration_per_scene > 10 and duration_per_scene <= 15):
        max_response_limit = 110
    elif (duration_per_scene > 15 and duration_per_scene <= 20):
        max_response_limit = 140
    # Get Total Scene From Duration
    total_scene = int(duration_total / duration_per_scene) # generate_video.calculate_scenes_and_images_simplified(duration)
    # Get All Description Or Content From Prompt According To Total Scene
    all_text_scene = [] # await generate_video.generate_scene_descriptions(prompt_text, total_scene, max_response_limit=max_response_limit)

    if array_text is not None and array_text != "":
        try:
            all_text_scene = json.loads(array_text) if array_text else []
        except:
            raise HTTPException(status_code=500, detail="Array Text Not Valid JSON Format")
    elif prompt_text is not None and prompt_text != "":
        all_text_scene = await generate_video.generate_scene_descriptions(prompt_text, total_scene, max_response_limit=max_response_limit)
    else:
        raise HTTPException(status_code=500, detail="No Array Text Or Prompt Text Found")
    # Get Image Or Video From Each Item Of Text Scene
    clips = []
    for each_text_scene_index, each_text_scene in enumerate(all_text_scene):
        all_audio_path = []
        if type == "video":
            print('this run')
            all_image_video_path = []
            vectorize = TfidfVectorizer(stop_words="english", ngram_range=(1,2))
            tfidf_matrix = vectorize.fit_transform([each_text_scene])
            feature_names = vectorize.get_feature_names_out()
            scores = tfidf_matrix.toarray().sum(axis=0)
            sorted_keywords = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
            """
            keyword = re.findall(r'\b\w+\b', each_text_scene.lower())
            """
            join_keyword = "+".join([word for word, score in sorted_keywords[:5]]) # "+".join([word for word, _ in Counter(keyword).most_common(4)])
            fetching_url = f"https://pixabay.com/api/videos/?key={os.getenv('PIXABAY_API_KEY')}&q={join_keyword}&video_type=animation"
            response = requests.get(fetching_url)
            data = response.json()
            if "hits" in data and len(data["hits"]) > 0:
                video_url = next((video for video in data["hits"] if 10 <= video["duration"] <= 20), None)["videos"]["large"]["url"]
                folder_path = "temp_videos"
                os.makedirs(folder_path, exist_ok=True)
                SAVE_PATH = os.path.join(folder_path, f"JOB_ID_{each_text_scene_index}_downloaded_video.mp4")
                video_response = requests.get(video_url, stream=True)
                with open(SAVE_PATH, "wb") as file:
                    for chunk in video_response.iter_content(chunk_size=1024):
                        file.write(chunk)
            all_image_video_path.append(os.path.abspath(SAVE_PATH))
        else:
            job_id_key = f"JOB_ID_{each_text_scene_index}"
            
            # Get Image in each sentence in One Scene.
            all_image_video_path = await process_scenes(each_text_scene, job_id_key)
            
            # Generate Audio in Each sentence in One Scene
        sentences = each_text_scene.split(". ")
        all_audio_path = (await text_to_speech.generate_text_to_speech_audio(sentences, voice))["data"]
        
        # Generate Audio Text Transcribe
        all_scene_text_transcription = (await text_to_speech.generate_timestamp_from_audio(all_audio_path))["data"]
        """
            total_scene = 6
            all_text_scene = [
                "A golden retriever named Max bounds through a sunlit park, his fur glistening against the emerald grass. He chases a fluttering butterfly, paws kicking up clumps of dirt, embodying pure joy.",
                "In a cozy living room, a scruffy terrier curls up on a worn-out sofa, head resting on a human’s lap. The gentle sound of a heartbeat lulls him to sleep as the owner strokes his fur absentmindedly.",
                "Rain pours down as a black Labrador splashes through puddles, droplets flying everywhere. He shakes off the water, grinning, as his owner laughs, holding a bright yellow umbrella.",
                "A timid beagle hides behind the legs of a little girl at the dog park. Encouraged by gentle pats, he gradually steps forward, sniffing at the grass, drawn to a wagging tail nearby.",
                "Under a starry night, a shepherd sits beside his owner on a porch swing, gazing up in silence. The moonlight casts a serene glow, illuminating the unshakeable bond between them.",
                "A group of puppies tumble over each other in a playful frenzy, their barks echoing in the air. Each one competes for the attention of a child, who giggles as they nuzzle and lick her hands.",
            ]
            all_image_video_path = [
                "example/images/JOB_ID_0_scene.png",
                "example/images/JOB_ID_1_scene.png",
                "example/images/JOB_ID_2_scene.png",
                "example/images/JOB_ID_3_scene.png",
                "example/images/JOB_ID_4_scene.png",
                "example/images/JOB_ID_5_scene.png",
            ]
            all_audio_path = [
                "example/audios/0-speech.mp3",
                "example/audios/1-speech.mp3",
                "example/audios/2-speech.mp3",
                "example/audios/3-speech.mp3",
                "example/audios/4-speech.mp3",
                "example/audios/5-speech.mp3",
            ]
            all_scene_text_transcription = [
                { "segments": [{ "start": 0, "end": 14, "text": all_text_scene[0] }] },
                { "segments": [{ "start": 0, "end": 14, "text": all_text_scene[1] }] },
                { "segments": [{ "start": 0, "end": 14, "text": all_text_scene[2] }] },
                { "segments": [{ "start": 0, "end": 14, "text": all_text_scene[3] }] },
                { "segments": [{ "start": 0, "end": 14, "text": all_text_scene[4] }] },
                { "segments": [{ "start": 0, "end": 14, "text": all_text_scene[5] }] },
            ]
            """
        # Generate Video Each Scene
        all_video_path = (await movie.combine_video_and_audio(target_width=1920, target_height=1080, type=type, duration_per_scene=duration_per_scene, total_scene=total_scene, all_image_video_path=all_image_video_path, all_audio_path=all_audio_path,all_scene_text_transcription=all_scene_text_transcription, font_size=font_size, font_color=font_color))
        scene_clips = [VideoFileClip(f).with_effects([vfx.CrossFadeIn(0.5), vfx.FadeOut(0.25)]) for f in all_video_path]  # Convert each file to a clip
        clips.extend(scene_clips)  # Store clips properly
    final_clip = concatenate_videoclips(clips, method="compose")
    # final_clip = CompositeVideoClip(clips)
    current_time = int(time() * 1000)
    temp_dir = "temp_videos"
    os.makedirs(temp_dir, exist_ok=True)
    final_output_path = os.path.join(temp_dir, f"{current_time}-final_concatenated_output.mp4")
    final_clip.write_videofile(final_output_path, codec="libx264", audio_codec="aac", fps=24)
    for clip in clips:
        clip.close()
    final_clip.close()
    return { "data": f"{str(request.base_url).rstrip('/')}/public/{current_time}-final_concatenated_output.mp4" }
