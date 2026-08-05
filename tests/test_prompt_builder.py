from app.services.prompt_builder import build_cover_letter_prompt, build_resume_prompt

CANDIDATE = {
    "professional_summary": "Operations leader",
    "skills": [{"value": "P&L management"}],
    "achievements": [{"value": "Managed 156 restaurants"}],
    "leadership_scope": [{"value": "Led regional teams"}],
    "career_tracks": ["Regional and Multi-Site Operations"],
}

def test_resume_prompt_contains_verified_evidence() -> None:
    _, prompt = build_resume_prompt(candidate_analysis=CANDIDATE, job_title="Operations Director", company="Example Co", job_description="Lead multi-site operations.", tone="professional", max_words=600)
    assert "Managed 156 restaurants" in prompt
    assert "Operations Director" in prompt

def test_cover_letter_prompt_contains_company_and_role() -> None:
    _, prompt = build_cover_letter_prompt(candidate_analysis=CANDIDATE, job_title="Head of Operations", company="Hospitality Co", job_description="Own P&L and delivery.", tone="confident", max_words=350)
    assert "Hospitality Co" in prompt
    assert "Head of Operations" in prompt
