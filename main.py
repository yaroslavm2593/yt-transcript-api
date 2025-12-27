from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)
import re
import os

app = FastAPI()

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
        "service": "YouTube Transcript API via ScrapingBee",
        "endpoint": "/get-transcript (POST)"
    }

@app.get("/debug")
def debug():
    """Диагностика настроек"""
    api_key = os.getenv("SCRAPINGBEE_API_KEY")
    
    return {
        "api_key_set": bool(api_key),
        "api_key_length": len(api_key) if api_key else 0,
        "api_key_preview": api_key[:20] + "..." if api_key else "NOT SET",
        "environment_check": "OK" if api_key else "FAILED - Check Render Environment Variables"
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
        # Получаем API key из переменных окружения
        api_key = os.getenv("SCRAPINGBEE_API_KEY")
        
        if not api_key:
            raise HTTPException(
                status_code=500, 
                detail="ScrapingBee API key not configured. Check /debug endpoint"
            )
        
        # Используем ScrapingBee как прокси для youtube-transcript-api
        proxies = {
            "http": f"http://{api_key}:render_js=False@proxy.scrapingbee.com:8886",
            "https": f"http://{api_key}:render_js=False@proxy.scrapingbee.com:8887"
        }
        
        # Создаем API с прокси
        ytt_api = YouTubeTranscriptApi(proxies=proxies)
        
        # Получаем транскрипт
        transcript = ytt_api.fetch(video_id, languages=['ru', 'en'])
        
        # Преобразуем в текст
        text = " ".join([snippet.text for snippet in transcript])
        
        return {
            "video_id": video_id,
            "language": transcript.language_code,
            "is_generated": transcript.is_generated,
            "transcript": text,
            "success": True,
            "method": "scrapingbee"
        }
        
    except TranscriptsDisabled:
        raise HTTPException(status_code=404, detail="Transcripts disabled for this video")
    except NoTranscriptFound:
        raise HTTPException(status_code=404, detail="No Russian or English transcript available")
    except VideoUnavailable:
        raise HTTPException(status_code=404, detail="Video unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
