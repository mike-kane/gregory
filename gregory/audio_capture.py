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
        """Play a short beep to signal that recording is open.

        Uses aplay (subprocess) rather than pygame so the ALSA device is fully
        released before pyaudio opens its capture stream — pygame holding the
        device open causes dsnoop to fail on the subsequent pa.open() call.
        Writes a proper WAV file so aplay can read format details from the header
        rather than relying on raw PCM flags which some adapters reject.
        """
        import subprocess
        import tempfile
        import wave as wave_mod

        rate = config.PYGAME_FREQUENCY  # confirmed working rate for this USB adapter
        freq = 880
        duration = 0.25
        n = int(rate * duration)
        t = np.arange(n) / rate
        tone = (np.sin(2 * np.pi * freq * t) * 16383).astype(np.int16)

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        try:
            with wave_mod.open(tmp.name, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(rate)
                wf.writeframes(tone.tobytes())
            result = subprocess.run(
                ["aplay", "-D", config.AUDIO_DEVICE, tmp.name],
                capture_output=True, timeout=3,
            )
            if result.returncode != 0:
                print(f"[beep] aplay failed: {result.stderr.decode().strip()}")
        except Exception as e:
            print(f"[beep] error: {e}")
        finally:
            os.unlink(tmp.name)

    def record_until_silence(self) -> str:
        """Record audio and return path to a temporary WAV file.

        Plays a beep, then measures ambient noise for 0.5 s to set an adaptive
        speech threshold (3× baseline). This makes detection robust to different
        mic gain levels and room noise floors without manual tuning.
        Silence detection only begins after speech is first detected.
        """
        self._play_ready_beep()

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
            frames.append(chunk)

            rms = np.sqrt(np.mean(np.frombuffer(chunk, dtype=np.int16).astype(np.float32) ** 2))
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
