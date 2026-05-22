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
import config
from gregory.motor_controller import MotorController, _gpio


def _verify_pin(pin, expected, label):
    actual = _gpio.input(pin)
    status = "OK" if actual == expected else f"WRONG (got {actual}, expected {expected})"
    print(f"  GPIO {pin} ({label}): {status}")


def test_mouth(motors: MotorController):
    print("Mouth: open for 1s, then close")
    motors.mouth_open()
    _verify_pin(config.MOUTH_AIN1, 0, "AIN1 should be LOW")
    _verify_pin(config.MOUTH_AIN2, 1, "AIN2 should be HIGH")
    time.sleep(1)
    motors.mouth_close()
    print("Mouth test done.")


def test_tail(motors: MotorController):
    print("Tail: wag for 3s")
    _gpio.output(config.TAIL_BIN1, False)
    _gpio.output(config.TAIL_BIN2, True)
    _verify_pin(config.TAIL_BIN1, 0, "BIN1 should be LOW")
    _verify_pin(config.TAIL_BIN2, 1, "BIN2 should be HIGH")
    _gpio.output(config.TAIL_BIN1, False)
    _gpio.output(config.TAIL_BIN2, False)
    motors.tail_wag_start()
    time.sleep(3)
    motors.tail_stop()
    print("Tail test done.")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "both"
    motors = MotorController()
    try:
        if arg in ("mouth", "both"):
            test_mouth(motors)
        if arg in ("tail", "both"):
            test_tail(motors)
    finally:
        motors.cleanup()
