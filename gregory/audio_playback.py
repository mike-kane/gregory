"""Play audio through the USB audio adapter, optionally syncing motors."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config

# Must be set before pygame is imported — SDL reads them at import time.
os.environ['SDL_AUDIODRIVER'] = 'alsa'
os.environ['AUDIODEV'] = config.AUDIO_DEVICE

import threading
import time
import pygame

# Initialise mixer once at import time using 44100 Hz — the rate ALSA hardware
# supports natively. Initialising at 16000 Hz causes ALSA to fall back to
# software resampling negotiation, which adds 10+ seconds on the Pi.
# pygame resamples audio files to this rate internally at negligible cost.
pygame.mixer.pre_init(frequency=44100, size=-16, channels=1, buffer=512)
pygame.mixer.init()


class AudioPlayer:
    def play_ack(self):
        """Play a short acknowledgement beep via aplay (no pygame init needed)."""
        import subprocess
        # aplay is available on Pi OS; on dev machines this will silently fail
        subprocess.run(
            ["aplay", "-D", config.AUDIO_DEVICE, "/usr/share/sounds/alsa/Front_Center.wav"],
            stderr=subprocess.DEVNULL,
        )

    def play_with_motors(self, audio_path: str, timeline: list, motors):
        """Play audio while driving motors according to the mouth timeline."""
        pygame.mixer.music.load(audio_path)

        frame_duration = 1.0 / config.MOTOR_FPS

        def motor_thread():
            for open_mouth in timeline:
                if open_mouth:
                    motors.mouth_open()
                else:
                    motors.mouth_close()
                time.sleep(frame_duration)
            motors.mouth_close()
            motors.tail_stop()

        motors.tail_wag_start()
        t = threading.Thread(target=motor_thread, daemon=True)
        t.start()

        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.01)

        t.join(timeout=2)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: python audio_playback.py <audio.mp3>")
        sys.exit(1)

    from mouth_sync import MouthSync
    from motor_controller import MotorController

    player = AudioPlayer()
    motors = MotorController()
    timeline = MouthSync(sys.argv[1]).build_timeline()
    player.play_with_motors(sys.argv[1], timeline, motors)
