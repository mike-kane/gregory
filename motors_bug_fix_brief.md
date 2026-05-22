## Bug fix: Motors don't work on second consecutive run of test_motors.py

### Symptom
Running test_motors.py works the first time after a power cycle, but subsequent 
runs without removing/reinserting batteries produce no motor movement.

### Cause
GPIO.cleanup() at the end of the test resets all pin states and modes. On the 
next run, GPIO.setmode() and GPIO.setup() are called again but the DRV8833 SLP 
pin (connected to Pi 3.3V) may be briefly floating during reinitialisation, 
putting the driver to sleep.

### Fix
In motor_controller.py, after GPIO.setmode() and GPIO.setup() calls in 
__init__, add a small delay and explicitly ensure the SLP pin is not being 
driven low. 

Also check whether GPIO.cleanup() should be removed or replaced with just 
setting all output pins LOW rather than full cleanup, since cleanup() 
de-initialises the GPIO library entirely and causes issues on subsequent runs 
in the same session.

### Acceptance criteria
- test_motors.py can be run multiple consecutive times without power cycling
- Motors respond correctly on every run