"""Record from the microphone until a silence timeout is reached."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tempfile
import wave
import pyaudio
import config


class AudioCapture:
    def record_until_silence(self) -> str:
        """Record audio and return path to a temporary WAV file."""
        pa = pyaudio.PyAudio()
        stream = pa.open(rate=16000, channels=1, format=pyaudio.paInt16,
                         input=True, input_device_index=config.AUDIO_INPUT_DEVICE,
                         frames_per_buffer=1024)

        frames = []
        silent_chunks = 0
        # How many consecutive silent chunks equal SILENCE_TIMEOUT seconds
        chunks_per_second = 16000 / 1024
        silence_limit = int(config.SILENCE_TIMEOUT * chunks_per_second)

        print("Recording...")
        while True:
            chunk = stream.read(1024, exception_on_overflow=False)
            frames.append(chunk)

            import audioop
            rms = audioop.rms(chunk, 2)
            if rms < config.SILENCE_THRESHOLD:
                silent_chunks += 1
            else:
                silent_chunks = 0

            if silent_chunks >= silence_limit and len(frames) > silence_limit:
                break

        stream.stop_stream()
        stream.close()
        pa.terminate()

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b"".join(frames))

        print(f"Saved recording to {tmp.name}")
        return tmp.name


if __name__ == "__main__":
    capture = AudioCapture()
    path = capture.record_until_silence()
    print(f"Recorded to: {path}")
