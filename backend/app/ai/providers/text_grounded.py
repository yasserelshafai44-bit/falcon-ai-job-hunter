import json

from app.ai.providers.text_base import TextGenerationProvider
from app.services.grounded_materials import render_material


class GroundedTextGenerationProvider(TextGenerationProvider):
    """Select and arrange verified source evidence without external generation."""

    name = "evidence_grounded"

    async def generate_text(self, *, system_prompt: str, user_prompt: str) -> str:
        return render_material(json.loads(user_prompt))
