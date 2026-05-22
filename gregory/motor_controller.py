"""DRV8833 motor control via GPIO. Stubs out gracefully on non-Pi hardware."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import threading
import time
import config

try:
    import RPi.GPIO as GPIO
    _HAS_GPIO = True
except ImportError:
    _HAS_GPIO = False


class MockGPIO:
    BCM = OUT = LOW = 0

    @staticmethod
    def setmode(_): pass

    @staticmethod
    def setwarnings(_): pass

    @staticmethod
    def setup(*_, **_kw): pass

    @staticmethod
    def output(pin, value):
        print(f"  [MockGPIO] pin {pin} → {value}")

    @staticmethod
    def cleanup(): pass


_gpio = GPIO if _HAS_GPIO else MockGPIO()

# RPi.GPIO can't reliably reinitialise within the same process after cleanup(),
# so we register it once here and never call it inside MotorController.
if _HAS_GPIO:
    import atexit
    atexit.register(GPIO.cleanup)


class MotorController:
    def __init__(self):
        _gpio.setmode(_gpio.BCM)
        _gpio.setwarnings(False)
        # initial=LOW prevents a brief undefined pin state during setup that
        # would cause an unexpected motor twitch.
        _gpio.setup(config.MOUTH_AIN1, _gpio.OUT, initial=_gpio.LOW)
        _gpio.setup(config.MOUTH_AIN2, _gpio.OUT, initial=_gpio.LOW)
        _gpio.setup(config.TAIL_BIN1,  _gpio.OUT, initial=_gpio.LOW)
        _gpio.setup(config.TAIL_BIN2,  _gpio.OUT, initial=_gpio.LOW)
        self._tail_thread = None
        self._tail_running = False

    def mouth_open(self):
        _gpio.output(config.MOUTH_AIN1, True)
        _gpio.output(config.MOUTH_AIN2, False)

    def mouth_close(self):
        _gpio.output(config.MOUTH_AIN1, False)
        _gpio.output(config.MOUTH_AIN2, False)

    def tail_wag_start(self):
        self._tail_running = True
        self._tail_thread = threading.Thread(target=self._tail_loop, daemon=True)
        self._tail_thread.start()

    def tail_stop(self):
        self._tail_running = False
        if self._tail_thread:
            self._tail_thread.join(timeout=1)
        _gpio.output(config.TAIL_BIN1, False)
        _gpio.output(config.TAIL_BIN2, False)

    def _tail_loop(self):
        while self._tail_running:
            _gpio.output(config.TAIL_BIN1, True)
            _gpio.output(config.TAIL_BIN2, False)
            time.sleep(0.4)
            _gpio.output(config.TAIL_BIN1, False)
            _gpio.output(config.TAIL_BIN2, True)
            time.sleep(0.4)

    def cleanup(self):
        self.tail_stop()
        self.mouth_close()


if __name__ == "__main__":
    motors = MotorController()
    print("Mouth open/close test:")
    motors.mouth_open()
    time.sleep(0.5)
    motors.mouth_close()
    time.sleep(0.2)

    print("Tail wag test (2 seconds):")
    motors.tail_wag_start()
    time.sleep(2)
    motors.tail_stop()

    motors.cleanup()
    print("Done.")
