from core.services.taxonomy import extract_skills

PREFERRED_HEADINGS = (
    "preferred",
    "preferred qualifications",
    "nice to have",
    "bonus",
    "pluses",
)

REQUIREMENT_HEADINGS = (
    "requirements",
    "qualifications",
    "minimum qualifications",
    "basic qualifications",
)

ALL_HEADINGS = tuple(sorted(set(PREFERRED_HEADINGS + REQUIREMENT_HEADINGS), key=len, reverse=True))


def _normalize_heading(line: str) -> str:
    return line.strip().lower().rstrip(":")


def _heading_type(line: str) -> str | None:
    normalized = _normalize_heading(line)
    for heading in ALL_HEADINGS:
        if normalized == heading:
            if heading in PREFERRED_HEADINGS:
                return "preferred"
            return "requirements"
    return None


def _extract_section(text: str, section_name: str) -> str:
    lines = text.splitlines()
    collected: list[str] = []
    capturing = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if capturing:
                collected.append("")
            continue

        current_heading = _heading_type(stripped)
        if current_heading is not None:
            if current_heading == section_name:
                capturing = True
                continue
            if capturing:
                break

        if capturing:
            collected.append(stripped)

    return "\n".join(collected).strip()


def parse_job_text(raw_text: str) -> dict[str, list[str]]:
    requirement_text = _extract_section(raw_text, "requirements")
    preferred_text = _extract_section(raw_text, "preferred")

    if not requirement_text:
        requirement_text = raw_text

    requirements = extract_skills(requirement_text)
    preferred = extract_skills(preferred_text)
    preferred = sorted(skill for skill in preferred if skill not in requirements)

    return {
        "requirements": requirements,
        "preferred": preferred,
    }
