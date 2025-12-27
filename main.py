from fastapi import FastAPI
from pydantic import BaseModel
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    CouldNotRetrieveTranscript,
)
from urllib.parse import urlparse, parse_qs
import re

app = FastAPI(title="YouTube Transcript API", version="1.0")

class TranscriptRequest(BaseModel):
    url: str

_YT_ID_RE = re.compile(
    r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|shorts/|embed/))([A-Za-z0-9_-]{6,})"
)

def extract_video_id(url: str) -> str | None:
    if not url:
        return None

    m = _YT_ID_RE.search(url)
    if m:
        return m.group(1)

    # fallback: watch?v=...
    try:
        parsed = urlparse(url)
        return parse_qs(parsed.query).get("v", [None])[0]
    except Exception:
        return None

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/get-transcript")
def get_transcript(data: TranscriptRequest):
    video_id = extract_video_id(data.url)
    if not video_id:
        return {"error": "Invalid YouTube URL"}

    try:
        items = YouTubeTranscriptApi.g
