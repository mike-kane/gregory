## Wake Word + Main Loop Implementation Brief

### Context

Gregory is a Raspberry Pi Zero 2W talking fish. The STT → LLM → TTS pipeline is fully
built and tested in `test_pipeline.py`. We now need to implement wake word detection and
the main loop that ties everything together into an always-on conversational system.

### What needs to be built

#### 1. `gregory/wake_word.py`

Implement wake word detection using openWakeWord.

- Load the openWakeWord model on init
- Expose a blocking `wait_for_wake_word()` method that listens continuously on the
  microphone until the wake phrase is detected, then returns
- Use `plughw:0,0` (card 0) for microphone input, consistent with the rest of the project
- Wake word model and threshold should come from `config.py`:

```python
  WAKE_WORD_MODEL = "hey_gregory"
  WAKE_WORD_THRESHOLD = 0.5
```

- openWakeWord works on raw 16kHz mono audio frames — feed it chunks from pyaudio
- Add an `if __name__ == "__main__"` block that runs `wait_for_wake_word()` in a loop
  and prints "Wake word detected!" each time, for standalone testing

Note: openWakeWord does not ship a "hey_gregory" model out of the box. Use the closest
available default model (e.g. "hey jarvis" or "alexa") as a placeholder for now, with
a comment noting it should be replaced with a custom trained model later. The model name
in config.py should make this easy to swap.

#### 2. Update `main.py`

Implement the main loop:

on startup:
initialise all components (wake word detector, mic, transcriber,
conversation, tts, player, motors)
play a short startup sound or print "Gregory is ready"
loop forever:
wait for wake word
play acknowledgement sound (short chime or "mm?" — configurable in config.py)
record speech until silence
transcribe via Whisper API
if transcript is empty or too short: go back to listening
get response from Claude API
synthesise response via ElevenLabs
play audio with motor sync
go back to listening
on Ctrl+C or exception:
stop motors (set all GPIO pins LOW)
clean up GPIO
exit cleanly

- All components should be initialised once at startup, not on each loop iteration
- Errors in the pipeline (API failures, network issues) should be caught, printed,
  and cause the loop to continue rather than crash Gregory entirely
- Conversation history should persist across turns within a single run session
- Add a configurable `CONVERSATION_TIMEOUT` in `config.py` — if the user hasn't spoken
  for this many seconds after a response, reset conversation history (start fresh)

#### 3. Auto-start on boot (systemd service)

Create `gregory.service` — a systemd unit file that starts Gregory automatically on boot:

```ini
[Unit]
Description=Gregory the Talking Fish
After=network.target sound.target

[Service]
Type=simple
User=gregory
WorkingDirectory=/home/gregory/gregory
Environment=SDL_AUDIODRIVER=alsa
Environment=AUDIODEV=plughw:1,0
ExecStart=/home/gregory/gregory/venv/bin/python main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Save this to the repo root. Include instructions in a comment at the top of the file
for how to install it:

```bash
sudo cp gregory.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gregory
sudo systemctl start gregory
```

### Config additions needed

Add to `config.py` if not already present:

```python
WAKE_WORD_MODEL = "hey_jarvis"       # placeholder — replace with custom model later
WAKE_WORD_THRESHOLD = 0.5
ACKNOWLEDGEMENT_SOUND = None         # path to a short WAV file, or None to skip
CONVERSATION_TIMEOUT = 30            # seconds before conversation history resets
```

### Acceptance criteria

- `python gregory/wake_word.py` runs standalone and prints "Wake word detected!" when
  the wake phrase is spoken
- `python main.py` starts up, waits silently, responds when wake word is spoken, and
  returns to listening after each response
- Ctrl+C exits cleanly with no GPIO errors
- `gregory.service` is present in the repo root and correctly structured

### Notes for Claude Code

- The ALSA warnings on startup are harmless — do not attempt to suppress them
- All existing modules (audio_capture, transcription, conversation, tts, audio_playback,
  motor_controller, mouth_sync) are already working — do not modify them unless
  necessary to support the main loop
- GPIO cleanup on exit is important — motors left in a non-zero state will drain the
  battery and could damage the DRV8833
- Test on the Pi, not a dev machine — wake word detection requires real microphone input
