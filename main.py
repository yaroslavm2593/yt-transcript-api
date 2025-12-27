from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)
import re
import os

app = FastAPI()

# Модель запроса
class TranscriptRequest(BaseModel):
    url: str

def extract_video_id(url: str):
    patterns = [r"v=([^&]+)", r"youtu\.be/([^?&]+)"]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "YouTube Transcript API with Webshare Proxy",
        "endpoint": "/get-transcript (POST)",
        "debug": "/debug (GET)"
    }

@app.get("/debug")
def debug():
    """Диагностика настроек прокси"""
    proxy_username = os.getenv("WEBSHARE_USERNAME")
    proxy_password = os.getenv("WEBSHARE_PASSWORD")
    
    return {
        "proxy_username_set": bool(proxy_username),
        "proxy_password_set": bool(proxy_password),
        "username_length": len(proxy_username) if proxy_username else 0,
        "password_length": len(proxy_password) if proxy_password else 0,
        "username_preview": proxy_username[:15] + "..." if proxy_username else "NOT SET",
        "environment_check": "OK" if proxy_username and proxy_password else "FAILED - Check Render Environment Variables"
    }

@app.post("/get-transcript")
def get_transcript(request: TranscriptRequest):
    url = request.url
    
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    video_id = extract_video_id(url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    
    try:
        # Получаем credentials из переменных окружения
        proxy_username = os.getenv("WEBSHARE_USERNAME")
        proxy_password = os.getenv("WEBSHARE_PASSWORD")
        
        if not proxy_username or not proxy_password:
            raise HTTPException(
                status_code=500, 
                detail="Proxy credentials not configured. Check /debug endpoint"
            )
        
        # Создаем API с Webshare прокси
        ytt_api = YouTubeTranscriptApi(
            proxy_config=WebshareProxyConfig(
                proxy_username=proxy_username,
                proxy_password=proxy_password
            )
        )
        
        # Получаем транскрипт
        transcript = ytt_api.fetch(video_id, languages=['ru', 'en'])
        
        # Преобразуем в текст
        text = " ".join([snippet.text for snippet in transcript])
        
        return {
            "video_id": video_id,
            "language": transcript.language_code,
            "is_generated": transcript.is_generated,
            "transcript": text,
            "success": True
        }
        
    except TranscriptsDisabled:
        raise HTTPException(status_code=404, detail="Transcripts disabled for this video")
    except NoTranscriptFound:
        raise HTTPException(status_code=404, detail="No Russian or English transcript available")
    except VideoUnavailable:
        raise HTTPException(status_code=404, detail="Video unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
