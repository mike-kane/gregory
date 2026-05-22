"""Verify motor wiring independently of the rest of the pipeline.

Usage:
  python tests/test_motors.py           # run both tests in sequence
  python tests/test_motors.py mouth     # mouth/head motor only
  python tests/test_motors.py tail      # tail motor only
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
from gregory.motor_controller import MotorController


def test_mouth(motors: MotorController):
    print("Mouth: open for 1s, then close")
    motors.mouth_open()
    time.sleep(1)
    motors.mouth_close()
    time.sleep(0.5)
    print("Mouth test done.")


def test_tail(motors: MotorController):
    print("Tail: wag for 3s")
    motors.tail_wag_start()
    time.sleep(3)
    motors.tail_stop()
    print("Tail test done.")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "both"
    motors = MotorController()
    print("Waiting 2s for driver to settle...")
    time.sleep(2)
    try:
        if arg in ("mouth", "both"):
            test_mouth(motors)
        if arg in ("tail", "both"):
            test_tail(motors)
    finally:
        motors.cleanup()
