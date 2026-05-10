"""Manage a multi-turn conversation with Claude."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import anthropic
import config


class Conversation:
    def __init__(self):
        self._client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self._history = []

    def send(self, user_text: str) -> str:
        self._history.append({"role": "user", "content": user_text})

        # Trim to keep only the most recent turns
        if len(self._history) > config.MAX_HISTORY_TURNS * 2:
            self._history = self._history[-(config.MAX_HISTORY_TURNS * 2):]

        kwargs = {
            "model": config.CLAUDE_MODEL,
            "max_tokens": config.MAX_RESPONSE_TOKENS,
            "messages": self._history,
        }

        if config.SYSTEM_PROMPT:
            # cache_control marks the system prompt for server-side caching.
            # Cost drops to ~10% of normal input token price on cache hits,
            # and latency improves — both matter on the Pi during live conversation.
            kwargs["system"] = [
                {
                    "type": "text",
                    "text": config.SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ]

        response = self._client.messages.create(**kwargs)
        reply = response.content[0].text
        self._history.append({"role": "assistant", "content": reply})

        # Log cache stats when available — useful during development to confirm hits
        usage = response.usage
        if hasattr(usage, "cache_read_input_tokens") and usage.cache_read_input_tokens:
            print(f"[cache hit: {usage.cache_read_input_tokens} tokens read from cache]")

        print(f"Gregory: {reply}")
        return reply


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    conv = Conversation()
    while True:
        try:
            user = input("You: ")
        except EOFError:
            break
        if not user.strip():
            break
        conv.send(user)  # send() already prints the reply
