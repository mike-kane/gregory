"""Wake word detection using openWakeWord."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pyaudio
import config

# openWakeWord processes 80 ms frames at 16 kHz
_FRAME_SAMPLES = 1280


class WakeWordDetector:
    def __init__(self):
        from openwakeword.model import Model
        # WAKE_WORD_MODEL is a placeholder ("hey_jarvis") until a custom
        # "hey_gregory" model is trained and dropped in here.
        self._model = Model(wakeword_models=[config.WAKE_WORD_MODEL])

    def wait_for_wake_word(self) -> None:
        """Block until the configured wake word is detected, then return."""
        pa = pyaudio.PyAudio()
        stream = pa.open(
            rate=16000, channels=1, format=pyaudio.paInt16,
            input=True, frames_per_buffer=_FRAME_SAMPLES,
        )
        print("Listening for wake word...")
        try:
            while True:
                chunk = stream.read(_FRAME_SAMPLES, exception_on_overflow=False)
                audio = np.frombuffer(chunk, dtype=np.int16)
                prediction = self._model.predict(audio)
                # Use max score across all loaded models — the dict key format
                # varies across openWakeWord versions, so avoid relying on the
                # exact key name matching WAKE_WORD_MODEL.
                if prediction and max(prediction.values()) > config.WAKE_WORD_THRESHOLD:
                    print("Wake word detected.")
                    return
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()


if __name__ == "__main__":
    detector = WakeWordDetector()
    print(f"Listening for '{config.WAKE_WORD_MODEL}' — say the wake word, then repeat.")
    while True:
        detector.wait_for_wake_word()
        print("Wake word detected!")
