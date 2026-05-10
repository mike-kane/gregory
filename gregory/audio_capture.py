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
    def _play_ready_beep(self) -> None:
        """Play a short beep through pygame to signal that recording is open.

        Best-effort: if pygame isn't initialised (e.g. standalone test run),
        we skip silently rather than crashing.
        """
        try:
            import pygame
            sample_rate = config.PYGAME_FREQUENCY
            duration = 0.2
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            tone = (np.sin(2 * np.pi * 880 * t) * 32767 * 0.5).astype(np.int16)
            # Mixer is initialised as stereo; make_sound needs matching shape.
            tone_data = np.column_stack([tone, tone]) if config.PYGAME_CHANNELS == 2 else tone
            sound = pygame.sndarray.make_sound(tone_data)
            sound.play()
            pygame.time.wait(int(duration * 1000) + 80)
        except Exception:
            pass

    def record_until_silence(self) -> str:
        """Record audio and return path to a temporary WAV file.

        Plays a beep before opening the mic so the speaker knows when to start.
        Silence detection only kicks in after actual speech is detected, so
        ambient quiet at the start of a recording never triggers an early exit.
        """
        self._play_ready_beep()

        pa = pyaudio.PyAudio()
        stream = pa.open(rate=16000, channels=1, format=pyaudio.paInt16,
                         input=True, frames_per_buffer=_CHUNK)

        frames = []
        silent_chunks = 0
        speech_detected = False
        silence_limit = int(config.SILENCE_TIMEOUT * 16000 / _CHUNK)

        print("Recording...")
        while True:
            chunk = stream.read(_CHUNK, exception_on_overflow=False)
            frames.append(chunk)

            # audioop was removed in Python 3.13 — compute RMS via numpy instead
            rms = np.sqrt(np.mean(np.frombuffer(chunk, dtype=np.int16).astype(np.float32) ** 2))
            if rms >= config.SILENCE_THRESHOLD:
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
