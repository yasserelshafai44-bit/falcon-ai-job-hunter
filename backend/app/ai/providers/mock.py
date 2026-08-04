from typing import TypeVar

from pydantic import BaseModel

from app.ai.providers.base import AIProvider

T = TypeVar("T", bound=BaseModel)


class MockAIProvider(AIProvider):
    """Deterministic provider for tests and local development."""

    def __init__(self, response: BaseModel) -> None:
        self._response = response

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        del system_prompt, user_prompt
        return response_model.model_validate(self._response.model_dump())
