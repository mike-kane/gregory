WAKE_WORD_MODEL = "hey_gregory"
SILENCE_THRESHOLD = 300         # minimum floor for adaptive threshold (see audio_capture.py)
MIC_GAIN = 4.0                  # software amplification — raise if mic doesn't pick up at distance
SILENCE_TIMEOUT = 1.2           # seconds of silence after speech before stopping
WHISPER_MODEL = "whisper-1"
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
SYSTEM_PROMPT = (
    "You are Gregory, a wisecracking animatronic largemouth bass mounted on a wall. "
    "You have strong opinions about everything. "
    "Reply in one or two punchy sentences only — you are a fish, not an essayist. "
    "Be dry, slightly snarky, and occasionally drop a fish pun when it fits naturally. "
    "Never explain your reasoning, never add caveats, and never apologize. "
    "If you don't know something, make a joke about it instead."
)
MAX_HISTORY_TURNS = 10
MAX_RESPONSE_TOKENS = 120       # hard ceiling; keeps replies short for voice
ELEVENLABS_VOICE_ID = "eVKQybPTL0poBPxBa8L6"
ELEVENLABS_MODEL_ID = "eleven_flash_v2_5"   # eleven_multilingual_v2 if flash unavailable
ELEVENLABS_SPEED = 1.2                      # 0.7–1.2; 1.0 = normal
TTS_CACHE_DIR = "/tmp/gregory_tts"
MOUTH_OPEN_THRESHOLD = 0.15
MOTOR_FPS = 50
MOUTH_AIN1 = 17
MOUTH_AIN2 = 27
TAIL_BIN1  = 22
TAIL_BIN2  = 23
AUDIO_DEVICE = "plughw:1,0"       # ALSA device string for pygame / aplay
PYGAME_FREQUENCY = 44000           # confirmed native rate for this USB audio adapter
PYGAME_CHANNELS  = 2              # stereo — mono (1) is often unsupported at hardware level
