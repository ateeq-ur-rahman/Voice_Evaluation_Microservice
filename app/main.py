
from fastapi import FastAPI, UploadFile, File, HTTPException
import requests
import time

app = FastAPI()

# Configuration
API_KEY = "283893d223fe4239829a63e725404dd4"
HEADERS = {
    "authorization": API_KEY,
    "content-type": "application/json"
}
MIN_CONFIDENCE = 0.85  # Threshold for acceptable pronunciation

@app.get("/")
def index():
    return {"message": "Welcome to the Voice Evaluation API"}

@app.post("/transcribe")
async def analyze_audio(file: UploadFile = File(...)):
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a .wav or .mp3 audio file.")

    try:
        # Step 1: Upload the audio file
        audio_bytes = await file.read()
        upload_resp = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers={"authorization": API_KEY},
            data=audio_bytes
        )

        if upload_resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to upload audio.")

        audio_url = upload_resp.json().get("upload_url")

        # Step 2: Request transcription with metadata
        transcript_payload = {
            "audio_url": audio_url,
            "punctuate": True,
            "format_text": True,
            "language_code": "en_us"
        }

        transcribe_resp = requests.post(
            "https://api.assemblyai.com/v2/transcript",
            headers=HEADERS,
            json=transcript_payload
        )

        if transcribe_resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Transcription request failed.")

        transcript_id = transcribe_resp.json().get("id")

        # Step 3: Poll until transcription is complete
        polling_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
        while True:
            poll_resp = requests.get(polling_url, headers=HEADERS)
            result = poll_resp.json()

            if result.get("status") == "completed":
                break
            elif result.get("status") == "error":
                raise HTTPException(status_code=500, detail="Transcription failed.")

            time.sleep(2)

        # Step 4: Extract word data
        words_info = result.get("words", [])
        words = [{
            "word": w["text"],
            "start": w["start"] / 1000,
            "end": w["end"] / 1000,
            "confidence": w["confidence"]
        } for w in words_info]

        audio_duration = words[-1]["end"] if words else 0

        # Step 5: Analyze pronunciation
        confidences = [w["confidence"] for w in words]
        avg_score = sum(confidences) / len(confidences) if confidences else 0
        pronunciation_score = round(avg_score * 100)

        mispronounced = [
            {
                "word": w["word"],
                "start": w["start"],
                "confidence": w["confidence"]
            }
            for w in words if w["confidence"] < MIN_CONFIDENCE
        ]

        # Step 6: Calculate pace
        total_words = len(words)
        wpm = round((total_words / audio_duration) * 60) if audio_duration > 0 else 0

        if wpm < 90:
            pace_feedback = "Too slow"
        elif wpm > 150:
            pace_feedback = "Too fast"
        else:
            pace_feedback = "Your speaking pace is appropriate."

        # Step 7: Detect pauses
        pause_count = 0
        total_pause_time = 0.0
        for i in range(1, total_words):
            pause = words[i]["start"] - words[i - 1]["end"]
            if pause > 0.5:
                pause_count += 1
                total_pause_time += pause

        if pause_count >= 5 or total_pause_time > 5:
            pause_feedback = "Too many or long pauses detected. Try to improve fluency."
        elif pause_count >= 2:
            pause_feedback = "Try to reduce long pauses to improve fluency."
        else:
            pause_feedback = "You maintained good fluency with minimal pauses."

        # Step 8: Construct natural language summary
        summary = []

        if wpm < 90:
            summary.append("You spoke a bit slowly.")
        elif wpm > 150:
            summary.append("You spoke a bit fast.")
        else:
            summary.append("You spoke at a good pace.")

        if mispronounced:
            unclear_words = ", ".join(w["word"] for w in mispronounced)
            summary.append(f"Focus on pronouncing '{unclear_words}' more clearly.")
        else:
            summary.append("Your pronunciation was generally clear.")

        if pause_count >= 2:
            summary.append("Consider reducing long pauses to improve fluency.")
        else:
            summary.append("You maintained good rhythm with minimal pauses.")

        feedback = " ".join(summary)

        return {
            "transcript": result.get("text", ""),
            "words": words,
            "audio_duration_sec": audio_duration,
            "pronunciation_score": pronunciation_score,
            "mispronounced_words": mispronounced,
            "pacing_wpm": wpm,
            "pacing_feedback": pace_feedback,
            "pause_count": pause_count,
            "total_pause_time_sec": round(total_pause_time, 2),
            "pause_feedback": pause_feedback,
            "text_feedback": feedback
        }

    except Exception as error:
        print("Error:", error)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during processing.")
