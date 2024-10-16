from sqlalchemy.ext.asyncio import AsyncSession
from google import generativeai as genai
# from google.generativeai.types import HarmCategory, HarmBlockThreshold

from .base import NMAdapterBase

class NMGeminiAdapter(NMAdapterBase):
    def __init__(self, apikey: str):
        self.model = 'gemini-1.5-pro-latest'
        self.instruction = ''
        genai.configure(api_key = apikey)

    """Compose message history
        history: [[ role, message ]]
        -> [{ role, parts }}]"""
    def _compose(self, history: list[tuple[str, str]], message: str) -> list[dict[str, str]]:
        result = []
        for [role, message] in history:
            assert role in [ 'user', 'assistant' ]
            result.append({
                'role': role,
                'parts': [ message ]
            })
        result.append({
            'role': 'user',
            'parts': [ message ]
        })
        return result

    def set_model(self, model: str):
        self.model = model

    def set_instruction(self, instruction: str):
        self.instruction = instruction
        
    # Chat completion
    #   -> (response, response_tokens, prompt_tokens)
    async def chat_completion(self, history: list, message: str) -> tuple[str, int, int]:
        return [ 'Gemini adapter disabled', 0, 0 ]
        model = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=self.instruction
        )

        response = await model.generate_content_async(
            self._compose(history, message),
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT : HarmBlockThreshold.BLOCK_NONE,
            }
        )

        return [ response.text, 0, 0 ]
    
