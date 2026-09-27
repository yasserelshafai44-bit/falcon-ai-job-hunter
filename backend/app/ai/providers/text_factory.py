from app.ai.providers.text_base import TextGenerationProvider
from app.ai.providers.text_grounded import GroundedTextGenerationProvider


def get_text_generation_provider() -> TextGenerationProvider:
    return GroundedTextGenerationProvider()
