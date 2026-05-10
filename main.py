"""
Entry point for Gregory. Runs the main wake-word → STT → LLM → TTS → motor loop.
"""

import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

import config


def main():
    from gregory.wake_word import WakeWordDetector
    from gregory.audio_capture import AudioCapture
    from gregory.transcription import Transcriber
    from gregory.conversation import Conversation
    from gregory.tts import TTS
    from gregory.mouth_sync import MouthSync
    from gregory.audio_playback import AudioPlayer
    from gregory.motor_controller import MotorController

    wake = WakeWordDetector()
    capture = AudioCapture()
    transcriber = Transcriber()
    conversation = Conversation()
    tts = TTS()
    player = AudioPlayer()
    motors = MotorController()

    last_response_time = None
    print("Gregory is ready. Listening for wake word.")

    try:
        while True:
            wake.wait_for_wake_word()

            # Reset conversation history if the user has been away long enough.
            if last_response_time is not None:
                if time.time() - last_response_time > config.CONVERSATION_TIMEOUT:
                    conversation.reset()
                    print("[conversation reset — timeout]")

            # Acknowledge wake word, then open mouth to signal we're listening.
            player.play_ack()
            motors.mouth_open()

            try:
                audio_path = capture.record_until_silence()
                motors.mouth_close()

                transcript = transcriber.transcribe(audio_path)
                if not transcript.strip():
                    continue

                print(f"You: {transcript}")
                response_text = conversation.send(transcript)
                tts_path = tts.synthesise(response_text)
                timeline = MouthSync(tts_path).build_timeline()
                player.play_with_motors(tts_path, timeline, motors)

                last_response_time = time.time()

            except Exception as e:
                print(f"[pipeline error] {e}", file=sys.stderr)
                # Ensure motors are in a safe state before continuing.
                try:
                    motors.tail_stop()
                    motors.mouth_close()
                except Exception:
                    pass

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        motors.cleanup()
        print("Gregory offline.")


if __name__ == "__main__":
    main()
