from abc import ABC, abstractmethod

class TextGenerationProvider(ABC):
    name: str

    @abstractmethod
    async def generate_text(self, *, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError
