"""Wake word detection using openWakeWord."""

import config


class WakeWordDetector:
    def __init__(self):
        import openwakeword
        self._model = openwakeword.Model(wakeword_models=[config.WAKE_WORD_MODEL])

    def wait_for_wake_word(self):
        """Block until the configured wake word is detected."""
        import pyaudio
        import numpy as np

        pa = pyaudio.PyAudio()
        stream = pa.open(rate=16000, channels=1, format=pyaudio.paInt16,
                         input=True, frames_per_buffer=1280)
        print("Listening for wake word...")
        try:
            while True:
                chunk = stream.read(1280, exception_on_overflow=False)
                audio = np.frombuffer(chunk, dtype=np.int16)
                prediction = self._model.predict(audio)
                if prediction.get(config.WAKE_WORD_MODEL, 0) > 0.5:
                    print("Wake word detected.")
                    return
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()


if __name__ == "__main__":
    detector = WakeWordDetector()
    print("Waiting for wake word once, then exiting.")
    detector.wait_for_wake_word()
    print("Done.")
