"""Text-to-speech via ElevenLabs API, with local caching."""

import hashlib
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config

os.makedirs(config.TTS_CACHE_DIR, exist_ok=True)


class TTS:
    def __init__(self):
        from elevenlabs.client import ElevenLabs
        self._client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

    def synthesise(self, text: str) -> str:
        """Return path to a cached or freshly generated MP3 file."""
        # Include generation params in the key so changing speed/model invalidates cache.
        cache_key_src = f"{text}|{config.ELEVENLABS_VOICE_ID}|{config.ELEVENLABS_MODEL_ID}|{config.ELEVENLABS_SPEED}"
        key = hashlib.sha256(cache_key_src.encode()).hexdigest()
        path = os.path.join(config.TTS_CACHE_DIR, f"{key}.mp3")

        if not os.path.exists(path):
            from elevenlabs import VoiceSettings
            audio = self._client.text_to_speech.convert(
                voice_id=config.ELEVENLABS_VOICE_ID,
                text=text,
                model_id=config.ELEVENLABS_MODEL_ID,
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    speed=config.ELEVENLABS_SPEED,
                ),
            )
            with open(path, "wb") as f:
                for chunk in audio:
                    if isinstance(chunk, bytes):
                        f.write(chunk)
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
