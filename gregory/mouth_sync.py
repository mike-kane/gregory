"""Analyse audio amplitude to produce a per-frame mouth open/close timeline."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import soundfile as sf
import config


class MouthSync:
    def __init__(self, audio_path: str):
        self._path = audio_path

    def build_timeline(self) -> list[bool]:
        """
        Return a list of booleans at MOTOR_FPS rate.
        True means mouth should be open for that frame.
        Uses soundfile+numpy instead of librosa to avoid numba JIT compilation,
        which adds 20+ seconds on first run on a Pi Zero 2W.
        """
        samples, sr = sf.read(self._path, dtype="float32", always_2d=False)
        if samples.ndim == 2:
            samples = samples.mean(axis=1)  # stereo → mono for amplitude analysis

        hop = max(1, int(sr / config.MOTOR_FPS))
        n_hops = len(samples) // hop

        rms_values = np.array([
            np.sqrt(np.mean(samples[i * hop:(i + 1) * hop] ** 2))
            for i in range(n_hops)
        ])

        max_rms = rms_values.max()
        if max_rms > 0:
            rms_values /= max_rms

        return [float(v) >= config.MOUTH_OPEN_THRESHOLD for v in rms_values]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python mouth_sync.py <audio_file>")
        sys.exit(1)

    ms = MouthSync(sys.argv[1])
    tl = ms.build_timeline()
    open_frames = sum(tl)
    print(f"{len(tl)} frames, {open_frames} open ({100 * open_frames // len(tl)}%)")
