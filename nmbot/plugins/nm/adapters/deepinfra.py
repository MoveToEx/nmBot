from openai import AsyncOpenAI
from .base import NMAdapterBase


class NMDeepInfraAdapter(NMAdapterBase):
    def __init__(self, apikey: str | None = None, model: str = 'meta-llama/Meta-Llama-3-70B-Instruct'):
        self.model = model
        self.instruction = ''
        self.api_key = apikey
        self.base_url = 'https://api.deepinfra.com/v1/openai'

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

    def set_api_key(self, api_key: str):
        self.api_key = api_key

    def is_available(self):
        return self.api_key is not None

    async def chat_completion(self, history: list[tuple[str, str]], message: str) -> tuple[str, int, int]:
        message = self._compose(history, message)
        client = AsyncOpenAI(base_url=self.base_url, api_key=self.api_key)

        response = await client.chat.completions.create(
            model=self.model,
            messages=message,
            stream=False
        )

        return (response.choices[0].message.content, response.usage.prompt_tokens, response.usage.completion_tokens)