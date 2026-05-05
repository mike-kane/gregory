"""Manage a multi-turn conversation with Claude."""

import os
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
            "max_tokens": 512,
            "messages": self._history,
        }
        if config.SYSTEM_PROMPT:
            kwargs["system"] = config.SYSTEM_PROMPT

        response = self._client.messages.create(**kwargs)
        reply = response.content[0].text
        self._history.append({"role": "assistant", "content": reply})
        print(f"Gregory: {reply}")
        return reply


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    conv = Conversation()
    while True:
        user = input("You: ")
        if not user.strip():
            break
        print(conv.send(user))
