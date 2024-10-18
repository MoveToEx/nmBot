class NMAdapterBase:
    def __init__(self, key: str):
        pass

    def set_model(self, model: str):
        raise NotImplementedError()
    
    def set_instruction(self, instruction: str):
        raise NotImplementedError()
    
    def set_api_key(self, api_key: str):
        raise NotImplementedError()
    
    def is_available(self) -> bool:
        raise NotImplementedError()

    async def chat_completion(self, history: list[tuple[str, str]], message: str) -> tuple[str, int, int]:
        raise NotImplementedError()