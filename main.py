"""
Entry point for Gregory. Runs the main wake-word → STT → LLM → TTS → motor loop.
"""

import os
from dotenv import load_dotenv

load_dotenv()


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

    print("Gregory is ready. Say 'Hey Gregory' to start.")

    while True:
        wake.wait_for_wake_word()
        player.play_ack()

        audio_path = capture.record_until_silence()
        transcript = transcriber.transcribe(audio_path)
        if not transcript.strip():
            continue

        response_text = conversation.send(transcript)
        audio_path = tts.synthesise(response_text)
        mouth_timeline = MouthSync(audio_path).build_timeline()

        player.play_with_motors(audio_path, mouth_timeline, motors)


if __name__ == "__main__":
    main()
