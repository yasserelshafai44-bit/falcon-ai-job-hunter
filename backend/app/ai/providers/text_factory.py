from app.ai.providers.text_base import TextGenerationProvider
from app.ai.providers.text_mock import MockTextGenerationProvider

def get_text_generation_provider() -> TextGenerationProvider:
    return MockTextGenerationProvider()
