from openai import AsyncOpenAI
from .base import NMAdapterBase


class NMDeepInfraAdapter(NMAdapterBase):
    def __init__(self, apikey: str):
        self.model: str = 'meta-llama/Meta-Llama-3-70B-Instruct'
        self.instruction: str = None
        self.client = AsyncOpenAI(
            api_key = apikey,
            base_url='https://api.deepinfra.com/v1/openai'
        )

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

    async def chat_completion(self, history: list[tuple[str, str]], message: str) -> tuple[str, int, int]:
        message = self._compose(history, message)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=message,
            stream=False
        )

        return (response.choices[0].message.content, response.usage.prompt_tokens, response.usage.completion_tokens)