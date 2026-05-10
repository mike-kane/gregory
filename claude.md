# Gregory

Gregory is a Raspberry Pi Zero 2W-powered talking fish (a modified Billy Big Mouth Bass) that listens for a wake word, records speech, sends it through an STT → LLM → TTS pipeline, and plays back the response while animating the fish's mouth and tail motors in sync with the audio.

---

## Hardware

- **Raspberry Pi Zero 2W** (with headers)
- **Adafruit DRV8833** dual DC motor driver breakout
- **Fermion 3W Mini Audio Stereo Amplifier** (PAM8403-based, DFRobot DFR0119)
- **USB Audio Adapter** (for audio output from Pi)
- **Mini USB Microphone** (for speech input)
- **Ethernet + USB Hub with Micro-USB OTG Connector**
- **MPM3610 5V Buck Converter** (powers Pi from fish battery compartment)
- **Fish motors** (DC, not servo):
  - Mouth motor → DRV8833 channel A (brown/black wires)
  - Tail motor → DRV8833 channel B (green/black wires)
- **Fish speaker** → Fermion amp output (blue wires)
- **On/off switch** → kept in circuit on power line from battery compartment

Full documentation on the hardware can be found in hardware.md.

### GPIO Pin Assignments (Pi Zero 2W)

```
DRV8833 AIN1  → GPIO 17
DRV8833 AIN2  → GPIO 27
DRV8833 BIN1  → GPIO 22
DRV8833 BIN2  → GPIO 23
DRV8833 VM    → battery voltage (via on/off switch)
DRV8833 GND   → common ground
DRV8833 VCC   → 3.3V from Pi
```

Audio output flows: Pi → USB audio adapter → Fermion amp → fish speaker.

---

## Project Structure

```
gregory/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── .env                        # API keys (never commit)
├── .env.example
├── config.py                   # All tuneable parameters in one place
├── main.py                     # Entry point - runs the main loop
├── gregory/
│   ├── __init__.py
│   ├── wake_word.py            # Wake word detection (openWakeWord)
│   ├── audio_capture.py        # Microphone recording until silence
│   ├── transcription.py        # STT via OpenAI Whisper API
│   ├── conversation.py         # Claude API conversation management
│   ├── tts.py                  # TTS via ElevenLabs API
│   ├── audio_playback.py       # Play audio through USB audio adapter
│   ├── motor_controller.py     # DRV8833 mouth/tail motor control via GPIO
│   └── mouth_sync.py           # Analyse audio amplitude → mouth timeline
└── tests/
    ├── test_motors.py           # Verify motor wiring independently
    ├── test_audio.py            # Verify mic input and speaker output
    └── test_pipeline.py        # End-to-end pipeline without motors
```

---

## Python Environment

- **Python 3.11+**
- **Dependency management:** `pip` + `requirements.txt`
- Always use a virtualenv: `python3 -m venv venv && source venv/bin/activate`
- Target platform is Raspberry Pi Zero 2W running Raspberry Pi OS Lite (64-bit)
- GPIO access via `RPi.GPIO` or `gpiozero`
- Some libraries (e.g. `RPi.GPIO`) are only available on the Pi — use mock/stub implementations when running on macOS/Linux dev machines

---

## Pipeline

```
[wake word detected]
        ↓
[record speech until silence]
        ↓
[Whisper API → transcript]
        ↓
[Claude API → response text]
        ↓
[ElevenLabs API → audio file]
        ↓
[analyse audio → mouth timeline]
        ↓
[play audio + animate motors in parallel]
        ↓
[return to wake word listening]
```

---

## Key Design Decisions

### Wake Word

- Use **openWakeWord** for local wake word detection (runs on Pi Zero 2W)
- Default wake phrase: "Hey Gregory"
- On detection: play a short acknowledgement sound, then begin recording

### Speech-to-Text

- Use **OpenAI Whisper API** (not local Whisper — too slow on Pi Zero)
- Record until silence is detected (energy threshold + silence timeout)
- Save to a temporary WAV file, send to Whisper, receive transcript

### LLM

- Use **Anthropic Claude API** (`claude-sonnet-4-20250514` or latest available)
- Maintain a conversation history list for multi-turn dialogue
- System prompt is loaded from `config.py` — no personality is hardcoded; fully configurable by the user
- Keep responses concise by default (this is a spoken conversation, not a text chat)

### Text-to-Speech

- Use **ElevenLabs API** for voice synthesis
- Voice ID is configurable in `config.py`
- Cache TTS responses locally by hash of input text to avoid repeat API calls for identical phrases

### Motor Control

- **Mouth motor**: driven by amplitude analysis of TTS audio output
  - Before playback, analyse audio with `librosa` to extract RMS energy per frame
  - Normalise to 0.0–1.0 range
  - During playback, a separate thread reads the timeline and pulses mouth motor at ~50fps
  - Threshold configurable in `config.py`
- **Tail motor**: wags periodically during responses (simple timed pattern, not audio-synced)
- Both motors use short pulses only — never driven continuously
- Motor direction: note which polarity opens vs closes mouth during hardware setup and record in `config.py`

### Audio Playback

- Use `pygame.mixer` or `aplay` subprocess for playback through USB audio adapter
- Playback and motor sync must run in parallel (threading)

---

## Configuration (config.py)

All tuneable parameters live here:

```python
WAKE_WORD_MODEL = "hey_gregory"
SILENCE_THRESHOLD = 500
SILENCE_TIMEOUT = 2.0
WHISPER_MODEL = "whisper-1"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
SYSTEM_PROMPT = ""              # Gregory's personality — set this to taste
MAX_HISTORY_TURNS = 10
ELEVENLABS_VOICE_ID = ""
TTS_CACHE_DIR = "/tmp/gregory_tts"
MOUTH_OPEN_THRESHOLD = 0.15
MOTOR_FPS = 50
MOUTH_AIN1 = 17
MOUTH_AIN2 = 27
TAIL_BIN1  = 22
TAIL_BIN2  = 23
AUDIO_DEVICE = "plughw:1,0"
```

---

## API Keys

Required in `.env`:

```
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
ELEVENLABS_API_KEY=
```

---

## Development Workflow

### On a dev machine (no Pi, no hardware)

- GPIO calls stub out automatically when `RPi.GPIO` is not importable
- Use `tests/test_pipeline.py` to run STT → LLM → TTS end-to-end through laptop speakers

### On the Pi

- SSH in via ethernet hub
- Run `python main.py` from within the virtualenv

### Order of bring-up

1. Test motors independently (`test_motors.py`)
2. Test mic input and speaker output (`test_audio.py`)
3. Test full pipeline without motors (`test_pipeline.py`)
4. Run `main.py` with motors enabled

---

## Dependencies (requirements.txt should include)

```
anthropic
openai
elevenlabs
openwakeword
pyaudio
librosa
numpy
RPi.GPIO
gpiozero
pygame
python-dotenv
```

---

## Notes for Claude Code

- Always prefer simple, readable code over cleverness — this is a hobby project
- Each module should be independently runnable for testing purposes
- Add `if __name__ == "__main__"` blocks to each module in `gregory/` for standalone testing
- Never hardcode API keys
- GPIO stub pattern: wrap all GPIO imports in try/except and provide a `MockGPIO` class for dev machine use
- Comments should explain _why_, not _what_
- When in doubt, make it configurable in `config.py` rather than hardcoding
