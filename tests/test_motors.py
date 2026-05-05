"""Verify motor wiring independently of the rest of the pipeline."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
from gregory.motor_controller import MotorController


def test_mouth():
    motors = MotorController()
    print("Mouth: open for 1s, then close")
    motors.mouth_open()
    time.sleep(1)
    motors.mouth_close()
    time.sleep(0.5)
    motors.cleanup()
    print("Mouth test done.")


def test_tail():
    motors = MotorController()
    print("Tail: wag for 3s")
    motors.tail_wag_start()
    time.sleep(3)
    motors.tail_stop()
    motors.cleanup()
    print("Tail test done.")


if __name__ == "__main__":
    test_mouth()
    test_tail()
