"""Text-to-speech via ElevenLabs API, with local caching."""

import hashlib
import os
import config

os.makedirs(config.TTS_CACHE_DIR, exist_ok=True)


class TTS:
    def __init__(self):
        from elevenlabs.client import ElevenLabs
        self._client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

    def synthesise(self, text: str) -> str:
        """Return path to a cached or freshly generated MP3 file."""
        key = hashlib.sha256(text.encode()).hexdigest()
        path = os.path.join(config.TTS_CACHE_DIR, f"{key}.mp3")

        if not os.path.exists(path):
            # convert() returns bytes directly in SDK v1+
            audio = self._client.text_to_speech.convert(
                voice_id=config.ELEVENLABS_VOICE_ID,
                text=text,
                model_id=config.ELEVENLABS_MODEL_ID,
            )
            with open(path, "wb") as f:
                f.write(audio)
            print(f"TTS cached to {path}")
        else:
            print(f"TTS cache hit: {path}")

        return path


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    tts = TTS()
    p = tts.synthesise("Hey there, I'm Gregory the fish!")
    print(f"Audio at: {p}")
