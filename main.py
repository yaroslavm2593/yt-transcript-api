from fastapi import FastAPI
from youtube_transcript_api import YouTubeTranscriptApi
import re

app = FastAPI()

def extract_video_id(url: str):
    match = re.search(r"(?:v=|youtu\.be/)([^&?/]+)", url)
    return match.group(1) if match else None

@app.get("/")
def root():
    return {"status": "ok", "service": "yt-transcript-api"}

@app.post("/get-transcript")
def get_transcript(data: dict):
    url = data.get("url")
    video_id = extract_video_id(url)

    if not video_id:
        return {"error": "Invalid YouTube URL"}

    try:
        api = YouTubeTranscriptApi()
        transcript = api.get_transcript(
            video_id,
            languages=["ru", "en"]
        )
        text = " ".join([x["text"] for x in transcript])
        return {"transcript": text}
    except Exception as e:
        return {"error": str(e)}
