import os
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse
from moviepy import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip, ImageClip, AudioFileClip, vfx
from moviepy.video.fx import CrossFadeIn
from PIL import Image, ImageDraw, ImageFont
from time import time
from typing import List
from . import text_to_speech
import numpy as np
import os
import shutil
import uuid

router = APIRouter(
    prefix="/movie",
    tags=["Movie"],
)

@router.post("/combine-video-and-audio")
async def movie_combination(file1: UploadFile = File(...), file2: UploadFile = File(...), text: str = Form(...)):
    return FileResponse(await combine_video_and_audio(file1, file2, text), media_type="video/mp4", filename="final_output.mp4")

@router.post("/combine-video-and-audio-multiple-concatenate")
async def movie_combination_multiple(file1: List[UploadFile] = File(...), file2: List[UploadFile] = File(...), text: List[str] = Form(...)):
    if not (len(file1) == len(file2) == len(text)):
        return { "data": "" }
    all_video = [await combine_video_and_audio(item_file1, item_file2, item_text) for item_file1, item_file2, item_text in zip(file1, file2, text)]
    return FileResponse(await concatenate_video(all_video), media_type="video/mp4", filename="concatenated_output.mp4")

async def concatenate_video(file: List[str]):
    try:
        clips = [VideoFileClip(f) for f in file]
        clips_with_transitions = [clips[i].with_effects([CrossFadeIn((1.0))]) if i > 0 else clips[i] for i in range(len(clips))]
        final_clip = concatenate_videoclips(clips_with_transitions, method="compose")
        current_time = int(time() * 1000)
        temp_dir = "temp_videos"
        os.makedirs(temp_dir, exist_ok=True)
        output_path = os.path.join(temp_dir, f"{current_time}-final_concatenated_output.mp4")
        final_clip.write_videofile(output_path, codec="libx264")
        for clip in clips:
            clip.close()
        final_clip.close()
        return output_path
    except Exception as e:
        print(f"An Error Occurred: {e}")
        return { "data": "" }

async def combine_video_and_audio(file1: UploadFile = File(...), file2: UploadFile = File(...), text: str = Form(...)):
    # Make Temporary Directory And Save The Video File
    current_time = int(time() * 1000)
    temp_dir = "temp_videos"
    os.makedirs(temp_dir, exist_ok=True)
    file1_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file1.filename}")
    file2_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file2.filename}")
    with open(file1_path, "wb") as buffer:
        shutil.copyfileobj(file1.file, buffer)
    with open(file2_path, "wb") as buffer:
        shutil.copyfileobj(file2.file, buffer)
    # Process The Video
    videoClip1 = VideoFileClip(file1_path)
    videoClip2 = VideoFileClip(file2_path)
    videoClip1 = videoClip1.without_audio()
    videoClip2 = videoClip2.without_audio()
    padding = 50
    total_width = videoClip1.size[0]
    video_width = videoClip2.resized(height=200).size[0]
    # Generate Audio From Text
    audios = await text_to_speech.generate_text_to_speech_audio([text])
    transcriptions = await text_to_speech.generate_timestamp_from_audio(audios.get("data", []))
    audioClip1 = AudioFileClip(audios.get("data", [])[0])
    videoClip1 = videoClip1.with_audio(audioClip1)
    # Add Text And Background Array Clip
    text_width = 400
    radius = 20
    all_text_clip = []
    all_background_clip = []
    for transcribe in transcriptions["data"][0]["segments"]:
        start_time = transcribe["start"]
        end_time = transcribe["end"]
        text_segmented = transcribe["text"]
        # Add Text Overlay
        text_overlay = TextClip(font=font_path, text=text_segmented, font_size=30, size=(text_width - 20, None), color="white", method="caption", text_align="right")
        text_overlay = text_overlay.with_position((total_width - padding - text_width + 10, "center"))
        """
        text_overlay = text_overlay.with_duration(videoClip1.duration)
        """
        text_overlay = text_overlay.with_start(start_time)
        text_overlay = text_overlay.with_end(end_time)
        all_text_clip.append(text_overlay)
        text_height = text_overlay.size[1]
        # Add A Background For The Text
        background_image = create_rounded_background(text_width, text_height + 40, radius, color=(0, 0, 0, 128))
        background_clip = ImageClip(background_image).with_position((total_width - padding - text_width, "center"))
        """
        background_clip = background_clip.with_duration(videoClip1.duration)
        """
        background_clip = background_clip.with_start(start_time)
        background_clip = background_clip.with_end(end_time)
        all_background_clip.append(background_clip)
    space_between = total_width - (padding * 2 + video_width + text_width)
    videoClip2_resized = videoClip2.resized(height=200).with_position((padding, "center"))
    result = CompositeVideoClip([videoClip1, videoClip2_resized, *all_background_clip, *all_text_clip], size=videoClip1.size)
    # Save The Final Video
    output_path = os.path.join(temp_dir, f"{current_time}-final_output.mp4")
    result.write_videofile(output_path, codec="libx264", audio_codec="aac")
    # Clean Up Temporary File
    videoClip1.close()
    videoClip2.close()
    result.close()
    os.remove(file1_path)
    os.remove(file2_path)
    return output_path

def create_rounded_background(width, height, radius, color):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (width, height)], radius=radius, fill=color)
    return np.array(img)

async def combine_video_and_audio(target_width: int, target_height: int,type: str, duration_per_scene: int, total_scene: int, all_image_video_path: List[str], all_audio_path: List[str], all_scene_text_transcription: list, font_size: int = 30, font_color: str = "white"):
    all_video_path = []
    for each_image_video_path_index, each_image_video_path in enumerate(all_image_video_path):
        image_video_clip = VideoFileClip(each_image_video_path) if type == "video" else ImageClip(each_image_video_path)
        audio_clip = AudioFileClip(all_audio_path[each_image_video_path_index])
        image_video_clip = image_video_clip.with_duration(max(audio_clip.duration) if type == "video" else audio_clip.duration)
        image_video_clip = image_video_clip.with_audio(audio_clip)
        scale_factor = max(target_width / image_video_clip.w, target_height / image_video_clip.h)
        image_video_clip = image_video_clip.resized(scale_factor)
        image_video_clip = image_video_clip.resized(lambda t: 1 + 0.02 * t)
        image_video_clip = image_video_clip.cropped(x_center=image_video_clip.w // 2, y_center=image_video_clip.h // 2, width=target_width, height=target_height)
        all_text_clip = []
        all_text_background_clip = []
        for transcribe in all_scene_text_transcription[each_image_video_path_index]["segments"]:
            start_time = transcribe["start"]
            end_time = transcribe["end"]
            text_segmented = transcribe["text"]
            text_overlay = TextClip(font=os.path.join(os.getcwd(), "src", "fonts", "TypeLightSans-KV84p.otf"), text=text_segmented, font_size=font_size, size=(380, None), color=font_color, method="caption", text_align="center")
            text_overlay = text_overlay.with_position(("center", image_video_clip.size[1] - text_overlay.size[1] - 40 + 15))
            text_overlay = text_overlay.with_start(start_time)
            text_overlay = text_overlay.with_end(end_time)
            all_text_clip.append(text_overlay)
            text_height = text_overlay.size[1]
            background_image = create_rounded_background(400, text_height + 40, 20, color=(0, 0, 0, 192))
            background_clip = ImageClip(background_image).with_position(("center", image_video_clip.size[1] - text_overlay.size[1] - 40 - 10))
            background_clip = background_clip.with_start(start_time)
            background_clip = background_clip.with_end(end_time)
            all_text_background_clip.append(background_clip)
        result = CompositeVideoClip([image_video_clip, *all_text_background_clip, *all_text_clip], size=image_video_clip.size)
        # Save Video To Storage
        temp_dir = "temp_videos"
        os.makedirs(temp_dir, exist_ok=True)
        current_time = int(time() * 1000)
        output_path = os.path.join(temp_dir, f"{current_time}-final_scene_output.mp4")
        result.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
        image_video_clip.close()
        audio_clip.close()
        for each_text_clip in all_text_clip:
            each_text_clip.close()
        for each_text_background_clip in all_text_background_clip:
            each_text_background_clip.close()
        result.close()
        all_video_path.append(output_path)
    return all_video_path
