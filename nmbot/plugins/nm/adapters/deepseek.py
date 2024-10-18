from openai import AsyncOpenAI
from .base import NMAdapterBase


class NMDeepSeekAdapter(NMAdapterBase):
    def __init__(self, apikey: str | None = None, model: str = 'deepseek-chat'):
        self.model = model
        self.instruction = ''
        self.api_key = apikey
        self.base_url = 'https://api.deepseek.com'

    def _compose(self, history: list[tuple[str, str]], prompt: str) -> list[dict]:
        result = []
        if self.instruction:
            result.append({
                'role': 'system',
                'content': self.instruction
            })
        for [role, message] in history:
            result.append({
                'role': role,
                'content': message
            })
        result.append({
            'role': 'user',
            'content': prompt
        })
        return result

    def set_model(self, model: str):
        self.model = model

    def set_instruction(self, instruction: str):
        self.instruction = instruction

    def set_api_key(self, api_key):
        self.api_key = api_key

    def is_available(self) -> bool:
        return self.api_key is not None

    async def chat_completion(self, history: list[tuple[str, str]], message: str) -> tuple[str, int, int]:
        message = self._compose(history, message)
        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

        response = await client.chat.completions.create(
            model=self.model,
            messages=message,
            stream=False
        )

        return (response.choices[0].message.content, response.usage.prompt_tokens, response.usage.completion_tokens)