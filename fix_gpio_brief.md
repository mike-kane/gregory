## Bug fix: GPIO pin numbering mode not set

### Error

test_motors.py fails on the tail motor test with:
`RuntimeError: Please set pin numbering mode using GPIO.setmode(GPIO.BOARD)
or GPIO.setmode(GPIO.BCM)`

### Fix

In `gregory/motor_controller.py`, add `GPIO.setmode(GPIO.BCM)` during GPIO
initialisation, before any GPIO.setup() calls. BCM mode means we refer to
pins by their GPIO number (e.g. GPIO 17) rather than their physical board
position, which is consistent with how pin numbers are defined in config.py.

### Acceptance criteria

- `python tests/test_motors.py` runs without errors
- Both mouth and tail motor tests complete successfully
