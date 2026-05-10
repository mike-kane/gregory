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
        """Record audio and return path to a temporary WAV file.

        Measures ambient noise for 0.5 s to set an adaptive speech threshold
        (3× baseline). Silence detection only begins after speech is first detected.
        In the full product, motor movement signals that Gregory is listening.
        """
        pa = pyaudio.PyAudio()
        stream = pa.open(rate=16000, channels=1, format=pyaudio.paInt16,
                         input=True, frames_per_buffer=_CHUNK)

        # Calibrate: measure ambient noise for 0.5 s while the room is still quiet.
        cal_chunks = int(0.5 * 16000 / _CHUNK)
        cal_data = b"".join(stream.read(_CHUNK, exception_on_overflow=False)
                            for _ in range(cal_chunks))
        baseline = np.sqrt(np.mean(
            np.frombuffer(cal_data, dtype=np.int16).astype(np.float32) ** 2
        ))
        # Floor from config prevents accidental triggers in near-silent rooms.
        threshold = max(config.SILENCE_THRESHOLD, baseline * 3.0)
        print(f"Baseline: {baseline:.0f} RMS  |  threshold: {threshold:.0f}  |  Recording...")

        frames = []
        silent_chunks = 0
        speech_detected = False
        silence_limit = int(config.SILENCE_TIMEOUT * 16000 / _CHUNK)

        while True:
            chunk = stream.read(_CHUNK, exception_on_overflow=False)

            # Apply software gain so a distant mic can still trigger detection.
            # Clip to int16 range to prevent wrap-around distortion.
            samples = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)
            samples = np.clip(samples * config.MIC_GAIN, -32768, 32767).astype(np.int16)
            frames.append(samples.tobytes())

            rms = np.sqrt(np.mean(samples.astype(np.float32) ** 2))
            if rms >= threshold:
                speech_detected = True
                silent_chunks = 0
            elif speech_detected:
                silent_chunks += 1

            if speech_detected and silent_chunks >= silence_limit:
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
