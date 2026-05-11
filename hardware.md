# Gregory Hardware Documentation

## Overview

Gregory is a modified Billy Big Mouth Bass (Amazon Alexa edition) driven by a Raspberry Pi
Zero 2W. The original Alexa control board has been removed and replaced with the Pi and a
small set of breakout boards that handle motor control, audio amplification, and power
regulation.

---

## Component List

| Component             | Model                                                    | Purpose                                  |
| --------------------- | -------------------------------------------------------- | ---------------------------------------- |
| Single board computer | Raspberry Pi Zero 2W (with headers)                      | Main compute, runs all software          |
| Motor driver          | Adafruit DRV8833 DC/Stepper Motor Driver Breakout        | Drives mouth and tail DC motors          |
| Audio amplifier       | DFRobot Fermion 3W Mini Stereo Amplifier (PAM8403)       | Amplifies audio output to fish speaker   |
| USB audio adapter     | Generic USB Audio Adapter (USB PnP Sound Device)         | Audio output interface from Pi           |
| Microphone            | Generic Mini USB Microphone (USB PnP Sound Device)       | Audio input for speech capture           |
| USB hub               | Ethernet + USB Hub with Micro-USB OTG Connector          | Provides USB ports + ethernet to Pi Zero |
| Buck converter        | Adafruit MPM3610 5V Buck Converter (21V in, 5V/1.2A out) | Regulates battery voltage to 5V for Pi   |
| Fish motors           | 2x DC motors (original BBMB hardware)                    | Mouth open/close, tail flap              |
| Fish speaker          | Small driver (original BBMB hardware, blue wires)        | Audio output                             |
| Power source          | 4x AA battery compartment (original BBMB hardware)       | Powers everything via on/off switch      |

---

## Physical Layout

All added electronics sit inside the fish's base/plaque cavity. The original Alexa PCB
has been removed. The on/off switch on the fish's back remains in circuit and cuts power
to everything.

---

## Power Architecture

4x AA batteries (~6V)
↓
on/off switch (original fish hardware, retained)
↓
┌───┴───────────────┐
│ │
MPM3610 VIN DRV8833 VM
(buck converter) (motor power)
│
MPM3610 VOUT (5V)
│
Pi Zero 2W (via cut micro USB cable, red→5V, black→GND)
All components share a common ground.

---

## Audio Architecture

Pi Zero 2W
│
└── USB hub (micro USB OTG)
├── USB audio adapter (card 1, plughw:1,0) ← output
│ │
│ Fermion amp (PAM8403)
│ │
│ Fish speaker (blue wires, original hardware)
│
└── USB microphone (card 0, plughw:0,0) ← input

### ALSA Device Assignments

- **Card 0** — USB microphone (capture only)
- **Card 1** — USB audio adapter (playback and capture, playback used)
- **Card 2** — Pi onboard HDMI audio (not used)

### pygame / SDL Audio

pygame requires the following environment variables set before import:

```python
os.environ['SDL_AUDIODRIVER'] = 'alsa'
os.environ['AUDIODEV'] = 'plughw:1,0'
```

These are set at the top of `audio_playback.py`. The device string comes from
`config.py` (`AUDIO_DEVICE`).

---

## Motor Architecture

### Motors

Both motors are small DC motors (not hobby servos) — original BBMB hardware.
They are driven by the DRV8833 via short PWM pulses, not continuously.

| Motor | Wire colours | DRV8833 channel         | GPIO pins                |
| ----- | ------------ | ----------------------- | ------------------------ |
| Mouth | brown/black  | Channel A (AOUT1/AOUT2) | AIN1=GPIO17, AIN2=GPIO27 |
| Tail  | green/black  | Channel B (BOUT1/BOUT2) | BIN1=GPIO22, BIN2=GPIO23 |

### DRV8833 Wiring

DRV8833 VCC → Pi 3.3V
DRV8833 GND → common ground
DRV8833 VM → battery voltage (post switch)
DRV8833 AIN1 → GPIO 17
DRV8833 AIN2 → GPIO 27
DRV8833 BIN1 → GPIO 22
DRV8833 BIN2 → GPIO 23
DRV8833 AOUT1/AOUT2 → mouth motor (brown/black)
DRV8833 BOUT1/BOUT2 → tail motor (green/black)

### Motor Behaviour

- **Mouth**: pulses in sync with TTS audio amplitude. RMS energy is extracted from
  the audio buffer before playback using librosa, normalised to 0.0–1.0, and used to
  drive the motor at ~50fps in a thread parallel to audio playback.
- **Tail**: wags on a simple timed pattern during responses, not audio-synced.
- Motors are never driven continuously — short pulses only to protect the DRV8833
  and avoid stalling.

### Motor Polarity

To be confirmed during hardware bring-up. Record which pin state (AIN1=HIGH/AIN2=LOW
vs AIN1=LOW/AIN2=HIGH) corresponds to mouth open vs mouth closed, and set accordingly
in `config.py`.

---

## GPIO Reference (Pi Zero 2W)

| GPIO    | Direction | Connected to | Purpose             |
| ------- | --------- | ------------ | ------------------- |
| GPIO 17 | Output    | DRV8833 AIN1 | Mouth motor forward |
| GPIO 27 | Output    | DRV8833 AIN2 | Mouth motor reverse |
| GPIO 22 | Output    | DRV8833 BIN1 | Tail motor forward  |
| GPIO 23 | Output    | DRV8833 BIN2 | Tail motor reverse  |

All other GPIO pins are unused.

---

## Required ALSA Configuration

Create `~/.asoundrc` on the Pi. Without this file, the ALSA `default` capture
device routes through the `dsnoop` sharing plugin, which corrupts its shared
memory after many pyaudio open/close cycles and produces "Illegal combination
of I/O devices" errors during wake word detection.

```
pcm.!default {
    type asym
    playback.pcm {
        type plug
        slave.pcm "hw:1,0"
    }
    capture.pcm {
        type plug
        slave.pcm "hw:0,0"
    }
}

ctl.!default {
    type hw
    card 1
}
```

This routes the default capture device to `plughw:0,0` (USB microphone, with
ALSA plug handling rate/format conversion) and default playback to `plughw:1,0`
(USB audio adapter), both without dsnoop or dmix.

---

## Known Quirks and Gotchas

- **ALSA warnings on startup** — a large block of ALSA warnings about unknown PCM
  devices prints on every run. These are harmless and relate to the Pi's ALSA config
  referencing hardware that doesn't exist (surround sound, HDMI audio etc). Ignore them.

- **Jack server warnings** — "Cannot connect to server socket" warnings from Jack audio
  are also harmless. Jack is not installed or used; pyaudio probes for it and fails
  silently.

- **pygame device init** — pygame must be told explicitly which ALSA device to use via
  environment variables before import, otherwise it fails with "No such file or directory".
  See audio architecture above.

- **pip installs on Pi Zero** — the Pi Zero's `/tmp` is a tmpfs in RAM (512MB total).
  Large pip installs can exhaust it. Use:

```bash
  mkdir -p ~/tmp ~/pip-cache
  export TMPDIR=~/tmp
  export PIP_CACHE_DIR=~/pip-cache
  pip install <package>
```

- **MPM3610 current limit** — the buck converter is rated 1.2A. The Pi Zero 2W draws
  up to ~700mA under load. Motors are powered directly from battery voltage, not through
  the buck converter, so there is adequate headroom. Do not power the motors from the
  MPM3610 output.

- **USB port on Pi Zero** — the Pi Zero 2W has two micro USB ports. The USB hub must
  connect to the port labelled `USB`, not `PWR`. Easy to mix up.
