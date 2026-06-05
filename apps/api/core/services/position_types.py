from __future__ import annotations

import re

from core.models import Job

DEFAULT_POSITION_TYPES = [Job.PositionType.INTERN]
RAW_TEXT_PREFIX_LENGTH = 2000

POSITION_TYPE_PATTERNS: list[tuple[str, tuple[re.Pattern[str], ...]]] = [
    (
        Job.PositionType.PART_TIME,
        (
            re.compile(r"\bpart[\s-]?time\b"),
        ),
    ),
    (
        Job.PositionType.INTERN,
        (
            re.compile(r"\bintern(ship)?s?\b"),
            re.compile(r"\bco[\s-]?op\b"),
        ),
    ),
    (
        Job.PositionType.FULL_TIME,
        (
            re.compile(r"\bfull[\s-]?time\b"),
            re.compile(r"\bnew grad\b"),
            re.compile(r"\bgraduate\b"),
        ),
    ),
]


def _build_search_text(*parts: str) -> str:
    return re.sub(r"\s+", " ", " ".join(part for part in parts if part)).strip().lower()


def _detect_matches(search_text: str) -> list[str]:
    matches: list[str] = []
    for position_type, patterns in POSITION_TYPE_PATTERNS:
        if any(pattern.search(search_text) for pattern in patterns):
            matches.append(position_type)
    return matches


def infer_position_type(*, title: str, location: str = "", raw_text: str = "", source_url: str = "") -> str:
    title_and_url_text = _build_search_text(title, source_url)
    title_and_url_matches = _detect_matches(title_and_url_text)
    if len(title_and_url_matches) == 1:
        return title_and_url_matches[0]
    if len(title_and_url_matches) > 1:
        return Job.PositionType.UNKNOWN

    raw_text_excerpt = raw_text[:RAW_TEXT_PREFIX_LENGTH]
    description_text = _build_search_text(title, location, raw_text_excerpt)
    description_matches = _detect_matches(description_text)
    if len(description_matches) == 1:
        return description_matches[0]

    return Job.PositionType.UNKNOWN


def infer_position_type_for_job(job: Job) -> str:
    return infer_position_type(
        title=job.title,
        location=job.location,
        raw_text=job.raw_text,
        source_url=job.source_url or "",
    )
