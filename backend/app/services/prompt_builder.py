from typing import Any

PROMPT_VERSION = "sprint7-v1"

def _values(items: list[dict[str, Any]]) -> list[str]:
    return [str(item.get("value") or "").strip() for item in items if str(item.get("value") or "").strip()]

def build_resume_prompt(*, candidate_analysis: dict[str, Any], job_title: str, company: str, job_description: str, tone: str, max_words: int) -> tuple[str, str]:
    system = (
        "You are a precise resume writer. Use only verified candidate evidence. "
        "Never invent employers, dates, qualifications, metrics, or achievements. Return plain text only."
    )
    skills = _values(candidate_analysis.get("skills", []))
    achievements = _values(candidate_analysis.get("achievements", []))
    leadership = _values(candidate_analysis.get("leadership_scope", []))
    tracks = [str(v).strip() for v in candidate_analysis.get("career_tracks", []) if str(v).strip()]
    user = f"""Create a tailored resume.

ROLE
Title: {job_title}
Company: {company}
Description:
{job_description}

VERIFIED EVIDENCE
Summary: {candidate_analysis.get("professional_summary", "")}
Skills:
- {"\n- ".join(skills) if skills else "No verified skills supplied"}
Achievements:
- {"\n- ".join(achievements) if achievements else "No verified achievements supplied"}
Leadership:
- {"\n- ".join(leadership) if leadership else "No verified leadership evidence supplied"}
Career tracks:
- {"\n- ".join(tracks) if tracks else "No career tracks supplied"}

CONSTRAINTS
Tone: {tone}
Maximum words: {max_words}
Preserve truth and chronology. Do not add unsupported qualifications.
Include professional summary, core competencies, selected achievements, and experience highlights.
""".strip()
    return system, user

def build_cover_letter_prompt(*, candidate_analysis: dict[str, Any], job_title: str, company: str, job_description: str, tone: str, max_words: int) -> tuple[str, str]:
    system = (
        "You are a concise cover-letter writer. Use only verified candidate evidence. "
        "Do not invent company facts or candidate claims. Return plain text only."
    )
    skills = _values(candidate_analysis.get("skills", []))
    achievements = _values(candidate_analysis.get("achievements", []))
    user = f"""Write a tailored cover letter.

ROLE
Title: {job_title}
Company: {company}
Description:
{job_description}

VERIFIED EVIDENCE
Summary: {candidate_analysis.get("professional_summary", "")}
Skills:
- {"\n- ".join(skills) if skills else "No verified skills supplied"}
Achievements:
- {"\n- ".join(achievements) if achievements else "No verified achievements supplied"}

CONSTRAINTS
Tone: {tone}
Maximum words: {max_words}
Explain fit using evidence. Do not fabricate company research.
""".strip()
    return system, user
