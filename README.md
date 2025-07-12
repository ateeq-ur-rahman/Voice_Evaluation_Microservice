Voice Evaluation Microservice
This project is a lightweight FastAPI-based microservice that performs voice evaluation on uploaded audio files. It utilizes AssemblyAI's transcription API to analyze pronunciation, pacing, and pause patterns. The service returns both quantitative metrics and qualitative feedback to help improve spoken English delivery.

Features
-> Transcribes audio files using AssemblyAI

-> Calculates a pronunciation score based on average word confidence

-> Identifies mispronounced words with timestamps and confidence scores

-> Computes speaking pace in Words Per Minute (WPM)

-> Detects long or frequent pauses between words

-> Generates human-readable feedback based on the analysis


Setup Instructions:

1) Clone the repository.

2) Install dependencies from requirement.txt.

3) Configure API key.

4) Run server command to be used  uvicorn app.main:app --reload

5) Access the API at: http://127.0.0.1:8000

Sample Audio File:
-> It is located in Sample_file directory.

Assumptions and notes:

-> This service is optimized for audio recordings in American English.

-> Words are flagged as mispronounced when their confidence score falls below a threshold of 0.85.

-> Pauses between words that exceed 0.5 seconds are treated as significant and factored into fluency evaluation.

-> A speaking rate under 90 words per minute is interpreted as slow, while over 150 WPM is categorized as fast.

-> Transcription is performed asynchronously by polling the AssemblyAI API until the process completes.

