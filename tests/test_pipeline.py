"""End-to-end pipeline test (no motors, no wake word) — runs on dev machine."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from gregory.audio_capture import AudioCapture
from gregory.transcription import Transcriber
from gregory.conversation import Conversation
from gregory.tts import TTS
from gregory.mouth_sync import MouthSync
from gregory.audio_playback import AudioPlayer
from gregory.motor_controller import MotorController


def run():
    capture = AudioCapture()
    transcriber = Transcriber()
    conversation = Conversation()
    tts = TTS()
    player = AudioPlayer()
    motors = MotorController()

    print("Speak your question (or stay silent to exit)...")
    audio_path = capture.record_until_silence()
    transcript = transcriber.transcribe(audio_path)

    if not transcript.strip():
        print("Nothing heard — exiting.")
        return

    response = conversation.send(transcript)
    tts_path = tts.synthesise(response)
    timeline = MouthSync(tts_path).build_timeline()
    player.play_with_motors(tts_path, timeline, motors)
    motors.cleanup()


if __name__ == "__main__":
    run()
