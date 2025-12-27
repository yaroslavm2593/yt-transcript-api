@app.post("/get-transcript")
def get_transcript(payload: dict):
    url = payload.get("url")
    if not url:
        return {"error": "URL is required"}

    video_id = extract_video_id(url)
    if not video_id:
        return {"error": "Invalid YouTube URL"}

    try:
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)

        transcript = None

        try:
            transcript = transcripts.find_manually_created_transcript(["ru", "en"])
        except:
            pass

        if transcript is None:
            try:
                transcript = transcripts.find_generated_transcript(["ru", "en"])
            except:
                pass

        if transcript is None:
            return {"error": "No suitable transcript found"}

        data = transcript.fetch()
        text = " ".join(x["text"] for x in data)

        return {
            "video_id": video_id,
            "language": transcript.language_code,
            "is_generated": transcript.is_generated,
            "transcript": text
        }

    except Exception as e:
        return {"error": str(e)}
