"""End-to-end pipeline test — runs on dev machine.

Usage:
  python test_pipeline.py                  # mic → STT → LLM → TTS → playback
  python test_pipeline.py --text "hello"   # skip mic/STT, type directly to LLM
  python test_pipeline.py --loop           # keep going until empty input
  python test_pipeline.py --text "hello" --loop
"""

import argparse
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from gregory.conversation import Conversation
from gregory.tts import TTS
from gregory.mouth_sync import MouthSync
from gregory.audio_playback import AudioPlayer
from gregory.motor_controller import MotorController


def get_transcript(text_arg: str | None) -> str:
    if text_arg is not None:
        return text_arg

    # Mic path — only import hardware modules when actually needed
    from gregory.audio_capture import AudioCapture
    from gregory.transcription import Transcriber

    capture = AudioCapture()
    transcriber = Transcriber()
    print("Speak your question...")
    audio_path = capture.record_until_silence()
    return transcriber.transcribe(audio_path)


def run_once(text_arg: str | None, conversation: Conversation, tts: TTS,
             player: AudioPlayer, motors: MotorController) -> bool:
    """Run one turn. Returns False if there was nothing to process."""
    if text_arg is None:
        transcript = get_transcript(None)
    else:
        transcript = text_arg

    if not transcript.strip():
        print("Nothing to send — exiting.")
        return False

    print(f"You: {transcript}")
    response = conversation.send(transcript)
    tts_path = tts.synthesise(response)
    timeline = MouthSync(tts_path).build_timeline()
    player.play_with_motors(tts_path, timeline, motors)
    return True


def main():
    parser = argparse.ArgumentParser(description="Gregory pipeline test")
    parser.add_argument("--text", metavar="TEXT",
                        help="Send this text directly instead of using the mic")
    parser.add_argument("--loop", action="store_true",
                        help="Keep running turns until empty input")
    args = parser.parse_args()

    conversation = Conversation()
    tts = TTS()
    player = AudioPlayer()
    motors = MotorController()

    if args.loop:
        while True:
            if args.text is not None:
                # Prompt for typed input each loop iteration
                typed = input("You: ").strip()
                if not typed:
                    break
                run_once(typed, conversation, tts, player, motors)
            else:
                if not run_once(None, conversation, tts, player, motors):
                    break
    else:
        run_once(args.text, conversation, tts, player, motors)

    motors.cleanup()


if __name__ == "__main__":
    main()
