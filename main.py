from fastapi import FastAPI
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)
import re

app = FastAPI(title="YouTube Transcript API", version="1.0.0")

# -------------------------
# utils
# -------------------------
def extract_video_id(url: str) -> str | None:
    """
    Извлекает video_id из YouTube URL
    """
    patterns = [
        r"v=([^&]+)",
        r"youtu\.be/([^?&]+)",
        r"v/([^?&]+)",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None

def transcript_to_text(transcript) -> str:
    """Склеивает список сегментов в один текст"""
    return " ".join(segment.get("text", "") for segment in transcript)

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
        return {"error": "Invalid YouTube URL"}

    try:
        # 1) Попробуем безопасный список и fetch/ручные/авто-транскрипты
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)

        # 2) Ищем ручной рус/англ сначала
        try:
            transcript = transcripts.find_manually_created_transcript(["ru", "en"])
            text = transcript.fetch()
            # transcript.fetch() может вернуть список сегментов или строку
            if isinstance(text, list):
                return {"transcript": transcript_to_text(text)}
            return {"transcript": text}
        except NoTranscriptFound:
            pass

        # 3) Ищем сгенерированные (авто) субтитры
        try:
            transcript = transcripts.find_generated_transcript(["ru", "en"])
            text = transcript.fetch()
            if isinstance(text, list):
                return {"transcript": transcript_to_text(text)}
            return {"transcript": text}
        except NoTranscriptFound:
            pass

        # 4) Фоллбек — fetch через экземпляр API (ещё вариант)
        api = YouTubeTranscriptApi()
        try:
            raw = api.fetch(video_id)  # или api.get_transcript в некоторых версиях
            return {"transcript": transcript_to_text(raw)}
        except Exception:
            # если fetch не работает — вернём понятную ошибку ниже
            raise

    except TranscriptsDisabled:
        return {"error": "Transcripts are disabled for this video"}
    except VideoUnavailable:
        return {"error": "Video is unavailable"}
    except NoTranscriptFound:
        return {"error": "No transcripts found"}
    except Exception as e:
        return {"error": str(e)}
