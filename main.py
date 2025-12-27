from fastapi import FastAPI
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)
import re

app = FastAPI(
    title="YouTube Transcript API",
    version="1.0.0"
)

# -------------------------
# utils
# -------------------------
def extract_video_id(url: str) -> str | None:
    """
    Извлекает video_id из YouTube URL
    """
    patterns = [
        r"v=([^&]+)",
        r"youtu\.be/([^?&]+)"
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def transcript_to_text(transcript) -> str:
    """
    Склеивает список сегментов в один текст
    """
    return " ".join(segment["text"] for segment in transcript)


# -------------------------
# routes
# -------------------------
@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/get-transcript")
def get_transcript(payload: dict):
    url = payload.get("url")
    if not url:
        return {"error": "URL is required"}

    video_id = extract_video_id(url)
    if not video_id:
        return {"error": "Invalid YouTu
