from sqlalchemy.ext.asyncio import AsyncSession

class NMAdapterBase:
    def __init__(self):
        pass

    def set_model(self, model: str):
        raise NotImplementedError()
    
    def set_instruction(self, instruction: str):
        raise NotImplementedError()

    async def chat_completion(self, history: list[tuple[str, str]], message: str) -> tuple[str, int]:
        raise NotImplementedError()