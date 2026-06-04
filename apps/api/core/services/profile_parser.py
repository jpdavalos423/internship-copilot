from core.services.taxonomy import extract_skills


def parse_profile_text(resume_text: str) -> list[str]:
    return extract_skills(resume_text)
