## Audio Playback Fix Brief

### Context
Gregory is a Raspberry Pi Zero 2W talking fish project. The STT → LLM → TTS pipeline is
built and tested. We have just completed audio hardware testing and identified two issues
that need fixing in the codebase.

### Hardware Environment
- Pi Zero 2W running Raspberry Pi OS Lite 64-bit (Python 3.13)
- USB microphone on card 0 (`plughw:0,0`)
- USB audio adapter on card 1 (`plughw:1,0`)
- Audio playback via pygame with ALSA

### Issues to Fix

#### 1. pygame device not found on init
`pygame.mixer.init()` fails with `ALSA: Couldn't open audio device: No such file or directory`
unless the following environment variables are set before pygame is imported:

```python
import os
os.environ['SDL_AUDIODRIVER'] = 'alsa'
os.environ['AUDIODEV'] = 'plughw:1,0'
```

These must be set before `import pygame` — setting them after has no effect.
The device string `plughw:1,0` should come from `config.py` (`AUDIO_DEVICE`), not be hardcoded.

Fix: set these env vars at the top of `audio_playback.py` before the pygame import,
pulling the device string from config.

#### 2. 15-second delay before playback begins
`pygame.mixer.init()` takes ~15 seconds because it probes and negotiates audio format with ALSA.

Fix: add a `pre_init` call before `init` to specify parameters explicitly:

```python
pygame.mixer.pre_init(frequency=16000, size=-16, channels=1, buffer=512)
pygame.mixer.init()
```

The recording sample rate is 16000Hz — ensure pygame is initialised at the same rate to
avoid format mismatch. Check `audio_capture.py` and confirm the `rate` parameter matches.

#### 3. Make audio devices configurable
`config.py` already has `AUDIO_DEVICE = "plughw:1,0"` but also needs:

```python
AUDIO_INPUT_DEVICE = 0   # USB microphone (card 0)
AUDIO_OUTPUT_DEVICE = 1  # USB audio adapter (card 1)
```

Ensure `audio_capture.py` uses `AUDIO_INPUT_DEVICE` and `audio_playback.py` uses
`AUDIO_OUTPUT_DEVICE` / `AUDIO_DEVICE` from config rather than any hardcoded values.

### Acceptance Criteria
- `python tests/test_audio.py` records audio and plays it back with no crash
- Playback begins within 1-2 seconds of the "Playing back through speaker..." message
- No hardcoded device strings anywhere outside `config.py`