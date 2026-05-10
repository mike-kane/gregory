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
        import glob
        import openwakeword
        from openwakeword.model import Model

        # Models are bundled as versioned .onnx files, e.g. hey_jarvis_v0.1.onnx.
        # Glob for any file matching the configured name so the version suffix
        # doesn't need to be hardcoded in config.py.
        # WAKE_WORD_MODEL is a placeholder until a custom "hey_gregory" model is trained.
        resources = os.path.join(os.path.dirname(openwakeword.__file__),
                                 "resources", "models")
        matches = glob.glob(os.path.join(resources, f"{config.WAKE_WORD_MODEL}*.onnx"))
        if not matches:
            raise FileNotFoundError(
                f"No model file found for '{config.WAKE_WORD_MODEL}' in {resources}"
            )
        self._model = Model(wakeword_model_paths=[matches[0]])

        # Keep one PyAudio instance alive for the detector's lifetime.
        # Calling pa.terminate() + PyAudio() between detections causes ALSA to
        # re-probe devices and can produce "Invalid sample rate" on subsequent calls.
        self._pa = pyaudio.PyAudio()
        # Bypass the ALSA 'default' PCM (which routes through dsnoop) by
        # targeting the hardware device for MIC_CARD directly. dsnoop's shared
        # memory gets into a bad state after many open/close cycles, causing
        # "Illegal combination of I/O devices" on the Nth detection.
        self._mic_index = self._find_mic_device_index()

    def _find_mic_device_index(self) -> int | None:
        """Return the portaudio device index for config.MIC_CARD, or None."""
        target = f"hw:{config.MIC_CARD},"
        for i in range(self._pa.get_device_count()):
            info = self._pa.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0 and target in info.get("name", ""):
                return i
        return None  # fall back to ALSA default if not found

    def wait_for_wake_word(self) -> None:
        """Block until the configured wake word is detected, then return."""
        stream = self._pa.open(
            rate=16000, channels=1, format=pyaudio.paInt16,
            input=True, frames_per_buffer=_FRAME_SAMPLES,
            input_device_index=self._mic_index,
        )
        print("Listening for wake word...")
        try:
            while True:
                chunk = stream.read(_FRAME_SAMPLES, exception_on_overflow=False)
                audio = np.frombuffer(chunk, dtype=np.int16)
                prediction = self._model.predict(audio)
                # Use max score across all loaded models — the dict key format
                # varies across openWakeWord versions so avoid relying on the
                # exact key name matching WAKE_WORD_MODEL.
                if prediction and max(prediction.values()) > config.WAKE_WORD_THRESHOLD:
                    print("Wake word detected.")
                    return
        finally:
            stream.stop_stream()
            stream.close()
            # Do NOT terminate self._pa here — reuse it on the next call.

    def close(self) -> None:
        """Release the PyAudio instance. Call once on shutdown."""
        self._pa.terminate()


if __name__ == "__main__":
    detector = WakeWordDetector()
    print(f"Listening for '{config.WAKE_WORD_MODEL}' — say the wake word, then repeat.")
    try:
        while True:
            detector.wait_for_wake_word()
            print("Wake word detected!")
    except KeyboardInterrupt:
        pass
    finally:
        detector.close()
