"""Speech-to-text via OpenAI Whisper API."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import openai
import config


class Transcriber:
    def __init__(self):
        self._client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def transcribe(self, audio_path: str) -> str:
        with open(audio_path, "rb") as f:
            result = self._client.audio.transcriptions.create(
                model=config.WHISPER_MODEL,
                file=f,
            )
        print(f"Transcript: {result.text}")
        return result.text


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: python transcription.py <audio.wav>")
        sys.exit(1)

    t = Transcriber()
    print(t.transcribe(sys.argv[1]))
