from fastapi import FastAPI
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)
import re

app = FastAPI()

def extract_video_id(url: str):
    patterns = [
        r"v=([^&]+)",
        r"youtu\.be/([^?&]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@app.get("/")
def root():
    return {"status": "ok", "service": "yt-transcript-api"}

@app.post("/get-transcript")
def get_transcript(data: dict):
    url = data.get("url")
    if not url:
        return {"error": "URL is required"}
    
    video_id = extract_video_id(url)
    if not video_id:
        return {"error": "Invalid YouTube URL"}
    
    try:
        # Создаем экземпляр API
        ytt_api = YouTubeTranscriptApi()
        
        # Получаем список доступных транскриптов
        transcript_list = ytt_api.list(video_id)
        
        # Ищем русский или английский транскрипт
        try:
            transcript = transcript_list.find_transcript(['ru', 'en'])
        except NoTranscriptFound:
            return {"error": "No Russian or English transcript available"}
        
        # Получаем текст
        fetched = transcript.fetch()
        text = " ".join([snippet["text"] for snippet in fetched])
        
        return {
            "video_id": video_id,
            "language": transcript.language_code,
            "is_generated": transcript.is_generated,
            "transcript": text
        }
        
    except TranscriptsDisabled:
        return {"error": "Transcripts are disabled for this video"}
    except VideoUnavailable:
        return {"error": "Video is unavailable"}
    except Exception as e:
        return {"error": f"Error: {str(e)}"}
