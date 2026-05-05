"""Verify microphone input and speaker output."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gregory.audio_capture import AudioCapture
from gregory.audio_playback import AudioPlayer
from gregory.motor_controller import MotorController
from gregory.mouth_sync import MouthSync


def test_record_and_play():
    print("Recording for up to ~5 seconds (speak now, then stay silent)...")
    capture = AudioCapture()
    path = capture.record_until_silence()
    print(f"Recorded: {path}")

    print("Playing back through speaker...")
    player = AudioPlayer()
    timeline = MouthSync(path).build_timeline()
    motors = MotorController()
    player.play_with_motors(path, timeline, motors)
    motors.cleanup()
    print("Playback done.")


if __name__ == "__main__":
    test_record_and_play()
