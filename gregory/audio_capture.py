"""Record from the microphone until a silence timeout is reached."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tempfile
import wave
import numpy as np
import pyaudio
import config

_CHUNK = 1024


class AudioCapture:
    def record_until_silence(self) -> str:
        """Record audio and return path to a temporary WAV file."""
        pa = pyaudio.PyAudio()
        stream = pa.open(rate=config.RECORD_RATE, channels=1, format=pyaudio.paInt16,
                         input=True, input_device_index=config.AUDIO_INPUT_DEVICE,
                         frames_per_buffer=_CHUNK)

        frames = []
        silent_chunks = 0
        # How many consecutive silent chunks equal SILENCE_TIMEOUT seconds
        silence_limit = int(config.SILENCE_TIMEOUT * config.RECORD_RATE / _CHUNK)

        print("Recording...")
        while True:
            chunk = stream.read(_CHUNK, exception_on_overflow=False)
            frames.append(chunk)

            # audioop was removed in Python 3.13 — compute RMS via numpy instead
            rms = np.sqrt(np.mean(np.frombuffer(chunk, dtype=np.int16).astype(np.float32) ** 2))
            if rms < config.SILENCE_THRESHOLD:
                silent_chunks += 1
            else:
                silent_chunks = 0

            if silent_chunks >= silence_limit and len(frames) > silence_limit:
                break

        stream.stop_stream()
        stream.close()
        pa.terminate()

        # Mic is mono; duplicate to stereo so pygame's stereo mixer plays at correct speed.
        mono = np.frombuffer(b"".join(frames), dtype=np.int16)
        stereo = np.column_stack((mono, mono)).flatten()

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(config.RECORD_RATE)
            wf.writeframes(stereo.tobytes())

        print(f"Saved recording to {tmp.name}")
        return tmp.name


if __name__ == "__main__":
    capture = AudioCapture()
    path = capture.record_until_silence()
    print(f"Recorded to: {path}")
