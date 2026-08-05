from app.ai.providers.text_base import TextGenerationProvider

class MockTextGenerationProvider(TextGenerationProvider):
    name = "mock"

    def __init__(self, response: str | None = None) -> None:
        self._response = response or (
            "Professional Summary\nEvidence-based operations leader tailored to the target role.\n\n"
            "Selected Achievements\n- Verified achievement included from candidate evidence."
        )

    async def generate_text(self, *, system_prompt: str, user_prompt: str) -> str:
        del system_prompt, user_prompt
        return self._response
