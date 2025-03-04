import os
import openai
import requests
import ffmpeg
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, APIRouter
from typing import List, Tuple
from requests.exceptions import RequestException, HTTPError, Timeout

load_dotenv()

# Constants
DALLE_IMAGE_SIZE = "1024x1024"
PORTRAIT_IMAGE_SIZE = "1080x1920"
LANDSCAPE_IMAGE_SIZE = "1920x1080"
FPS = 24
BACKGROUND_WIDTH = 1920
BACKGROUND_HEIGHT = 1080
NUM_SCENES = 5
MAX_RESPONSE_LENGTH = 100

# OpenAI and API Key Configurations
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/video", tags=["Video"])

@router.post("/generate-scene", response_model=List[str])
async def generate_scene_descriptions(prompt: str, num_scenes: int = NUM_SCENES, max_response_limit: int = MAX_RESPONSE_LENGTH) -> List[str]:
    """Generate scene descriptions using OpenAI."""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages= [
                {"role": "developer", "content": [{"type": "text", "text": "You are a creative screenwriter that writes description about scenes based on prompts keyword from user.  Limit each scene description to {max_response_limit} characters"}]},
                {"role": "user", "content": [{"type": "text", "text": f"Write {num_scenes} short scene descriptions for: {prompt}"}]}
            ],
        )

         # Extract content from the first choice
        # logger.info(f"OpenAI Response: {response}")
        content = response.choices[0].message.content
        logger.info(f"OpenAI Response Content: {content}")

        # Split the content into individual scenes (assuming double newlines separate scenes)
        scenes = [scene.strip() for scene in content.split("\n\n") if scene.strip()]
        # scenes = [scene[:MAX_RESPONSE_LENGTH].strip() for scene in content.split("\n\n") if scene.strip()]

        # Success log after scenes are generated
        logger.info(f"Successfully generated {len(scenes)} scenes for prompt: {prompt}")
        print(f"Scenes successfully generated") 

        return scenes  # Return the scenes as a list of strings
    except Exception as e:
        logger.error(f"Scene generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scene generation failed: {str(e)}")

# @router.post("/generate-image")
# async def generate_images_from_scenes(scene: str, job_id: str) -> str:
#     """Generate images using DALL-E from scene descriptions."""
#     try:
#         response = openai.images.generate(
#             model="dall-e-3",
#             prompt=scene,
#             n=1,
#             size=DALLE_IMAGE_SIZE,
#             quality="standard"
#         )
#         image_url = response.data[0].url
#         image_path = f"temp_images/{job_id}_scene.png"
#         os.makedirs(os.path.dirname(image_path), exist_ok=True)

#         # Handling image download with retries and timeout
#         try:
#             img_response = requests.get(image_url, timeout=10)
#             img_response.raise_for_status()  # Check for successful response
#             with open(image_path, "wb") as f:
#                 f.write(img_response.content)

#              # Success log after image is saved
#             logger.info(f"Image successfully generated and saved at {image_path}")
#             print(f"Image successfully generated and saved at {image_path}")  # Optionally print to the console

#         except (RequestException, HTTPError, Timeout) as e:
#             logger.error(f"Failed to download image: {e}")
#             raise HTTPException(status_code=500, detail=f"Failed to download image: {str(e)}")

#         return image_path  # Return the path to the saved image

#     except Exception as e:
#         logger.error(f"Image generation failed: {e}")
#         raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

async def acceded_character(scene:str) -> str:
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages= [
            {"role": "system", "content": [{"type": "text", "text": "You will be provided with a main text, and your task is to extract a keyword from it. This value may exceed in below 20 characters."}]},
            {"role": "user", "content": [{"type": "text", "text": f"{scene}"}]}
        ],
    )
    return { 'data': response.choices[0].message.content or "" }

# @router.post("/generate-image")
# async def generate_images_from_scenes(scene: str, job_id: str, orientation: str = "portrait") -> str:
#     """
#     Generate images using DALL-E from scene descriptions.
#     Orientation can be 'portrait' or 'landscape'.
#     """
#     try:
#         # Determine image size based on orientation
#         if orientation.lower() == "portrait":
#             image_size = PORTRAIT_IMAGE_SIZE
#         elif orientation.lower() == "landscape":
#             image_size = LANDSCAPE_IMAGE_SIZE
#         elif orientation.lower() == "square":
#             image_size = DALLE_IMAGE_SIZE
#         else:
#             raise HTTPException(
#                 status_code=400, 
#                 detail="Invalid orientation. Please use 'portrait' or 'landscape'."
#             )

#         # Generate the image with DALL-E
#         response = openai.images.generate(
#             model="dall-e-3",
#             prompt=scene,
#             n=1,
#             size=image_size,
#             quality="standard"
#         )
#         image_url = response.data[0].url
#         image_path = f"temp_images/{job_id}_scene.png"
#         os.makedirs(os.path.dirname(image_path), exist_ok=True)

#         # Handling image download with retries and timeout
#         try:
#             img_response = requests.get(image_url, timeout=10)
#             img_response.raise_for_status()  # Check for successful response
#             with open(image_path, "wb") as f:
#                 f.write(img_response.content)

#             # Success log after image is saved
#             logger.info(f"Image successfully generated and saved at {image_path}")
#             print(f"Image successfully generated and saved at {image_path}")  # Optionally print to the console

#         except (RequestException, HTTPError, Timeout) as e:
#             logger.error(f"Failed to download image: {e}")
#             raise HTTPException(status_code=500, detail=f"Failed to download image: {str(e)}")

#         return image_path  # Return the path to the saved image

#     except Exception as e:
#         logger.error(f"Image generation failed: {e}")
#         raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


@router.post("/generate-image")
async def generate_images_from_scenes(scene: str, job_id: str, orientation: str = "portrait") -> str:
    """
    Generate images using DALL-E from scene descriptions.
    Orientation can be 'portrait' or 'landscape'.
    """
    try:
        # Determine image size based on orientation
        if orientation.lower() == "portrait":
            image_size = PORTRAIT_IMAGE_SIZE
        elif orientation.lower() == "landscape":
            image_size = LANDSCAPE_IMAGE_SIZE
        elif orientation.lower() == "square":
            image_size = DALLE_IMAGE_SIZE
        else:
            raise HTTPException(
                status_code=400, 
                detail="Invalid orientation. Please use 'portrait' or 'landscape'."
            )

        # Generate the image with DALL-E
        # response = openai.images.generate(
        #     model="dall-e-3",
        #     prompt=scene,
        #     n=1,
        #     size=image_size,
        #     quality="standard"
        # ))
        # Generate the image with Pixabay
        summarize_scene = await acceded_character(scene)
        fetching_url = f"https://pixabay.com/api/?key={os.getenv('PIXABAY_API_KEY')}&q={summarize_scene['data']}&orientation={image_size}"

        # Fetch the data from Pixabay API
        response = requests.get(fetching_url)
        data = response.json()
        if "hits" in data and len(data["hits"]) > 0:
            first_item = next(iter(data["hits"]), None)  # Get the first item safely
            if first_item:  # Ensure it's not None
                image_url = first_item.get("webformatURL")
                print("image_url: ", image_url)
                image_path = f"temp_images/{job_id}_scene.png"
                os.makedirs(os.path.dirname(image_path), exist_ok=True)

                # Handling image download with retries and timeout
                try:
                    img_response = requests.get(image_url, timeout=10)
                    img_response.raise_for_status()  # Check for successful response
                    with open(image_path, "wb") as f:
                        f.write(img_response.content)

                    # Success log after image is saved
                    logger.info(f"Image successfully generated and saved at {image_path}")
                    print(f"Image successfully generated and saved at {image_path}")  # Optionally print to the console

                except (RequestException, HTTPError, Timeout) as e:
                    logger.error(f"Failed to download image: {e}")
                    raise HTTPException(status_code=500, detail=f"Failed to download image: {str(e)}")

                return image_path  # Return the path to the saved image

        else:
            # If no images were found, log an error and raise an exception
            logger.error("No image found for the given scene.")
            raise HTTPException(status_code=500, detail="No image found for the given scene.")


    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


# utils function for calculate total scene and image duration
def calculate_scenes_and_images_simplified(total_duration: int) -> Tuple[int, int]:
    """
    Calculate the number of scenes and total images needed based on the total video length.
    Simplified method: every 30 seconds corresponds to 10 scenes.
    
    Args:
        total_duration (int): Total duration of the video in seconds.
        
    Returns:
        Tuple[int, int]: A tuple containing (number_of_scenes, total_images_needed).
    """
    # Number of scenes per 30 seconds
    scenes_per_30_seconds = 2

    # Calculate the number of scenes based on total duration
    number_of_scenes = (total_duration // 30) * scenes_per_30_seconds

    # Calculate total images (assuming each scene generates 1 image for simplicity)
    total_images_needed = number_of_scenes

    return number_of_scenes, total_images_needed


@router.post("/create-video")
def create_video_from_images(
    input_folder: str,
    output_folder: str,
    total_duration: int = 60,  # Default duration of 60 seconds
    fps: int = 30  # Default FPS of 30
) -> str:
    """
    Create a video from images in a folder using FFmpeg.
    Args:
        input_folder (str): Path to the folder containing images.
        output_folder (str): Path to the folder where the video will be saved.
        total_duration (int): Total duration of the video in seconds. Defaults to 60 seconds.
        fps (int): Frames per second for the video. Defaults to 30 FPS.
    Returns:
        str: Path to the created video file.
    """
    try:
        # Get all image files from the input folder
        valid_extensions = (".png", ".jpeg", ".jpg")
        image_paths = [
            os.path.join(input_folder, f)
            for f in sorted(os.listdir(input_folder))
            if f.lower().endswith(valid_extensions)
        ]

        if not image_paths:
            raise HTTPException(status_code=400, detail="No valid images found in the input folder.")

        # Calculate duration per image
        scene_duration = total_duration / len(image_paths)

        # Prepare FFmpeg input streams
        input_file = os.path.join(input_folder, "input_images.txt")
        with open(input_file, "w") as f:
            for path in image_paths:
                f.write(f"file '{os.path.abspath(path)}'\n")
                f.write(f"duration {scene_duration}\n")

        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)
        output_path = os.path.join(output_folder, "output_video.mp4")

        # Use FFmpeg to create the video
        ffmpeg.input(input_file, format="concat", safe=0).output(
            output_path,
            vcodec="libx264",
            pix_fmt="yuv420p",
            r=fps
        ).run(overwrite_output=True)


        logger.info(f"Video created successfully at {output_path}")
        print(f"Video created successfully at {output_path}")  # Optionally print to the console

        return output_path

    except Exception as e:
        logger.error(f"Video creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Video creation failed: {str(e)}")

@router.post("/generate-background")
def generate_background_video(job_id: str, total_duration: int, fps: int, width: int = BACKGROUND_WIDTH, height: int = BACKGROUND_HEIGHT) -> str:
    """Generate a geometric background video."""
    background_path = f"backgrounds/{job_id}_background.mp4"
    try:
        stream = (
            ffmpeg
            .input(f"nullsrc=s={width}x{height}:d={total_duration}:r={fps}", f="lavfi")
            .filter("mandelbrot", rate=0.02)
            .filter("colorize", hue=240, saturation=0.8, lightness=0.5)
            .filter("scale", width, height)
            .output(background_path, vcodec="libx264", pix_fmt="yuv420p")
        )
        ffmpeg.run(stream, overwrite_output=True)
        return background_path
    except Exception as e:
        logger.error(f"Background generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Background generation failed: {str(e)}")


@router.post("/overlay")
def overlay_videos(background_path: str, image_video_path: str, output_path: str, inner_width: int, inner_height: int):
    """Overlay the image video onto the background video."""
    try:
        x_offset = (BACKGROUND_WIDTH - inner_width) // 2
        y_offset = (BACKGROUND_HEIGHT - inner_height) // 2

        final_stream = (
            ffmpeg.input(background_path)
            .overlay(ffmpeg.input(image_video_path).filter("scale", inner_width, inner_height), x=x_offset, y=y_offset)
            .output(output_path, vcodec="libx264", pix_fmt="yuv420p", shortest=None)
        )
        ffmpeg.run(final_stream, overwrite_output=True)
        return output_path
    except Exception as e:
        logger.error(f"Overlay video creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Overlay video creation failed: {str(e)}")


@router.post("/generate-video/")
async def generate_video(prompt: str, fps: int = FPS, style: str = "geometric", total_duration: int = 60):
    """
    Generate a final video from a user prompt with scenes, images, and background overlay.
    """
    job_id = ''.join(e for e in prompt.replace(" ", "_")[:10] if e.isalnum())  # Generate a safe job ID

    try:
        scenes = await generate_scene_descriptions(prompt)
        image_paths = await generate_images_from_scenes(scenes, job_id)
        image_video_path = f"videos/{job_id}_image_video.mp4"
        os.makedirs(os.path.dirname(image_video_path), exist_ok=True)
        create_video_from_images(image_paths, image_video_path, total_duration, fps)
        background_video_path = generate_background_video(job_id, total_duration, fps)
        final_video_path = f"videos/{job_id}_final_video.mp4"
        overlay_videos(background_video_path, image_video_path, final_video_path, 1280, 720)
        return {"message": "Video created successfully", "video_path": final_video_path}
    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")


# Example usage for a POST request to generate a video

# import requests

# prompt = "A futuristic city with towering skyscrapers"
# url = "http://127.0.0.1:8000/generate-video/"  # Adjust the URL to your FastAPI server

# response = requests.post(url, json={"prompt": prompt, "fps": 24, "style": "geometric", "total_duration": 60})

# if response.status_code == 200:
#     print("Video created successfully!")
#     print("Video path:", response.json()["video_path"])
# else:
#     print("Error:", response.json()["detail"])