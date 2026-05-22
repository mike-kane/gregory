"""Verify motor wiring independently of the rest of the pipeline.

Tests each motor in both directions with short pulses. This lets you identify
the correct polarity without stalling the DRV8833 into thermal shutdown.

Watch each motor as the script runs and note which direction label (A or B)
produces the expected movement — open for mouth, wag for tail.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
import config
from gregory.motor_controller import MotorController, _gpio

PULSE = 0.4   # seconds per burst — short enough to stop before a stall builds heat
COAST = 0.3   # coast time between direction changes


def _pulse(pin_a, val_a, pin_b, val_b, label):
    print(f"  {label}")
    _gpio.output(pin_a, val_a)
    _gpio.output(pin_b, val_b)
    time.sleep(PULSE)
    _gpio.output(pin_a, False)
    _gpio.output(pin_b, False)
    time.sleep(COAST)


def test_mouth(motors: MotorController):
    print("\n=== MOUTH MOTOR ===")
    print("Watch the mouth and note which direction opens it:")
    _pulse(config.MOUTH_AIN1, True,  config.MOUTH_AIN2, False, "A: AIN1=HIGH, AIN2=LOW")
    _pulse(config.MOUTH_AIN1, False, config.MOUTH_AIN2, True,  "B: AIN1=LOW,  AIN2=HIGH")
    print("Mouth done — record which label (A or B) opened the mouth.")


def test_tail(motors: MotorController):
    print("\n=== TAIL MOTOR ===")
    print("Watch the tail and note which direction moves it:")
    _pulse(config.TAIL_BIN1, True,  config.TAIL_BIN2, False, "A: BIN1=HIGH, BIN2=LOW")
    _pulse(config.TAIL_BIN1, False, config.TAIL_BIN2, True,  "B: BIN1=LOW,  BIN2=HIGH")
    print("Wag pattern for 2s:")
    motors.tail_wag_start()
    time.sleep(2)
    motors.tail_stop()
    print("Tail done.")


if __name__ == "__main__":
    motors = MotorController()
    try:
        test_mouth(motors)
        print("\n(Pausing 3s for driver to cool...)")
        time.sleep(3)
        test_tail(motors)
    finally:
        motors.cleanup()
