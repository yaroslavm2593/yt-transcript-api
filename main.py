from fastapi import FastAPI
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)
import re

app = FastAPI(title="YouTube Transcript API")

def extract_video_id(url: str) -> str | None:
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

@app.post("/get-transcript")
def get_transcript(payload: dict):
    url = payload.get("url")
    if not url:
        return {"error": "URL is required"}

    video_id = extract_video_id(url)
    if not video_id:
        return {"error": "Invalid YouTube URL"}

    try:
        transcript = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=["ru", "en"]
        )
        text = " ".join(item["text"] for item in transcript)
        return {"transcript": text}

    except TranscriptsDisabled:
        return {"error": "Transcripts are disabled"}
    except NoTranscriptFound:
        return {"error": "No transcript found"}
    except VideoUnavailable:
        return {"error": "Video unavailable"}
    except Exception as e:
        return {"error": str(e)}
