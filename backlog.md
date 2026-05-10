# Gregory — Backlog

Items discovered during first end-to-end pipeline test. Listed roughly by dependency order, not priority.

---

## 1. Ready signal before listening begins

**Problem:** There is no clear cue that the system is ready for input. The speaker does not know when to start talking.

**Current state:** `test_pipeline.py` plays a short beep (via `aplay`) immediately before `AudioCapture.record_until_silence()` opens the mic. This works for testing.

**What still needs doing:**
- Wire the same beep into `main.py`'s wake-word-detected → record transition so the full product has the same cue.
- When motors are integrated, supplement or replace the beep with a physical gesture: the mouth motor opens and holds (or the tail gives a single wag) to indicate Gregory is listening. This is more natural for a fish than a beep.

**Files to touch:** `main.py`, `motor_controller.py`

---

## 2. Silence detection is too sensitive

**Problem:** After the speaker finished talking, the recorder kept running for ~15 seconds due to ambient noise exceeding `SILENCE_THRESHOLD`. The pipeline did not advance until the room was essentially silent.

**What to try (in order of simplicity):**
1. **Raise `SILENCE_THRESHOLD` in `config.py`** — current value is `500`. Try `800`–`1500` and test in the actual room environment. This is the first thing to tune.
2. **Require speech-first before the silence timer starts** — already implemented (the `speech_detected` flag in `audio_capture.py`). Confirm it is working as intended.
3. **Shorten `SILENCE_TIMEOUT`** — currently `2.0` seconds. `1.0`–`1.2` s is enough for natural speech pauses and will feel more responsive.
4. **Replace energy-based VAD with a model-based one** — libraries like `silero-vad` or `webrtcvad` are accurate at distinguishing speech from background noise regardless of absolute amplitude. This is the robust long-term solution if threshold tuning is not enough.

**Files to touch:** `config.py` (threshold + timeout), `gregory/audio_capture.py` (VAD implementation if going model-based)

---

## 3. End-to-end latency is too high

**Problem:** The gap between the speaker finishing a sentence and Gregory beginning to respond is long enough to break conversational flow.

**Contributing stages (each adds latency):**
- Whisper API round-trip
- Claude API round-trip
- ElevenLabs TTS generation + download
- Audio file load and playback start

**What to try:**
1. **Switch to a faster LLM.** `claude-haiku-4-5-20251001` is significantly faster than Sonnet for short conversational responses. Update `CLAUDE_MODEL` in `config.py`. Evaluate response quality — if acceptable, keep it.
2. **Stream ElevenLabs audio.** The ElevenLabs Python SDK supports streaming audio chunks. Start playing the first chunk while the rest is still generating rather than waiting for the full file. This is the single biggest latency win on the TTS side.
3. **Cache common responses.** Already stubbed in `tts.py` via `TTS_CACHE_DIR`. Verify it is actually being used for repeated phrases (e.g. acknowledgement sounds, greetings).
4. **Reduce Whisper timeout.** If the recorded audio is short, Whisper returns quickly. The silence detection fix (item 2) will help here indirectly by not sending long recordings of ambient noise.
5. **Overlap stages where possible.** Once Claude returns the response text, ElevenLabs generation can start while mouth-sync analysis is being set up. Look for serial waits that could be parallelised.

**Files to touch:** `config.py` (`CLAUDE_MODEL`), `gregory/tts.py` (streaming), `gregory/audio_playback.py` (streaming playback), `gregory/conversation.py` (model config)

---

## 4. Speech playback is too slow

**Problem:** The ElevenLabs voice sounds unnaturally slow — not the pacing of a quick, conversational fish.

**What to try:**
1. **Set ElevenLabs `speed` parameter.** The ElevenLabs v3 API accepts a `speed` float (1.0 = normal, up to ~1.5 before quality degrades). Add a `ELEVENLABS_SPEED` config value and pass it in `tts.py`'s `generate()` call.
2. **Tune voice stability/style settings.** Lower stability can produce a more animated, faster-feeling delivery. Expose `stability` and `similarity_boost` in `config.py` if not already there.
3. **Post-process with ffmpeg/librosa speed-up.** As a last resort, resample the audio faster after generation. Adds a step but is model-agnostic.

**Files to touch:** `config.py` (speed + voice settings), `gregory/tts.py`

---

## 5. Responses are too verbose

**Problem:** Gregory's replies are essay-length. For a voice interface — and especially for a novelty animatronic fish — responses need to be short, punchy, and fun.

**What to do:**
- Rewrite `SYSTEM_PROMPT` in `config.py`. Key instructions to include:
  - Respond in one or two sentences maximum.
  - Prefer quippy, slightly snarky, fish-themed wit.
  - Never explain your reasoning or add caveats.
  - If you don't know something, make a joke about it instead of saying "I don't know."
- Optionally add a `max_tokens` cap to the Claude API call in `conversation.py` as a hard ceiling (e.g. 80–120 tokens).

**Files to touch:** `config.py` (`SYSTEM_PROMPT`), `gregory/conversation.py` (optional `max_tokens`)

---

## 6. (Stretch) Barge-in / interruption support

**Problem:** Once Gregory starts speaking, the speaker cannot interrupt him — they have to wait for the full response to finish before the next turn begins. This feels robotic compared to modern voice assistants.

**Approach:**
- Run wake-word detection (or a simpler energy-based voice detector) in a background thread during playback.
- When voice activity is detected above threshold while audio is playing, stop `pygame.mixer.music`, stop the motor thread, and immediately transition to the recording state.
- The cleanest implementation is a shared `threading.Event` called `stop_playback` that the motor thread, music player, and main loop all watch.

**Complexity:** Medium-high. Requires threading changes across `audio_playback.py`, `motor_controller.py`, and `main.py`. Audio and motor teardown must be clean to avoid state bleed into the next turn.

**Files to touch:** `gregory/audio_playback.py`, `gregory/motor_controller.py`, `main.py`
