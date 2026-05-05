"""Analyse audio amplitude to produce a per-frame mouth open/close timeline."""

import numpy as np
import librosa
import config


class MouthSync:
    def __init__(self, audio_path: str):
        self._path = audio_path

    def build_timeline(self) -> list[bool]:
        """
        Return a list of booleans at MOTOR_FPS rate.
        True means mouth should be open for that frame.
        """
        y, sr = librosa.load(self._path, sr=None, mono=True)
        hop_length = int(sr / config.MOTOR_FPS)
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]

        # Normalise so the loudest frame = 1.0
        max_rms = rms.max()
        if max_rms > 0:
            rms = rms / max_rms

        timeline = [float(v) >= config.MOUTH_OPEN_THRESHOLD for v in rms]
        return timeline


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python mouth_sync.py <audio.mp3>")
        sys.exit(1)

    ms = MouthSync(sys.argv[1])
    tl = ms.build_timeline()
    open_frames = sum(tl)
    print(f"{len(tl)} frames, {open_frames} open ({100*open_frames//len(tl)}%)")
