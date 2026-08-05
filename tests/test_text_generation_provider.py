import pytest
from app.ai.providers.text_mock import MockTextGenerationProvider

@pytest.mark.asyncio
async def test_mock_text_provider_is_deterministic() -> None:
    provider = MockTextGenerationProvider("Generated content")
    assert await provider.generate_text(system_prompt="a", user_prompt="b") == "Generated content"
    assert await provider.generate_text(system_prompt="x", user_prompt="y") == "Generated content"
