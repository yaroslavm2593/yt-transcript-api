from fastapi import FastAPI
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    TooManyRequests
)
import re

app = FastAPI()

def extract_video_id(url: str):
    patterns = [r"v=([^&]+)", r"youtu\.be/([^?&]+)"]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@app.get("/")
def root():
    return {"status": "ok", "service": "YouTube Transcript API"}

@app.post("/get-transcript")
def get_transcript(data: dict):
    url = data.get("url")
    if not url:
        return {"error": "URL is required"}
    
    video_id = extract_video_id(url)
    if not video_id:
        return {"error": "Invalid YouTube URL"}
    
    try:
        # Получаем транскрипт
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id, languages=['ru', 'en'])
        
        # Преобразуем в текст (используем .text вместо ["text"])
        text = " ".join([snippet.text for snippet in transcript])
        
        return {
            "video_id": video_id,
            "language": transcript.language_code,
            "is_generated": transcript.is_generated,
            "transcript": text
        }
        
    except TranscriptsDisabled:
        return {"error": "Transcripts disabled for this video"}
    except NoTranscriptFound:
        return {"error": "No Russian or English transcript available"}
    except VideoUnavailable:
        return {"error": "Video unavailable"}
    except TooManyRequests:
        return {"error": "YouTube blocked request (too many requests)"}
    except Exception as e:
        return {"error": f"Error: {str(e)}"}
