from __future__ import annotations

import re

from core.models import Job

DEFAULT_POSITION_TYPES = [Job.PositionType.INTERN]

POSITION_TYPE_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    (
        Job.PositionType.PART_TIME,
        ("part-time", "part time"),
    ),
    (
        Job.PositionType.INTERN,
        ("intern", "internship", "co-op", "coop"),
    ),
    (
        Job.PositionType.FULL_TIME,
        ("full-time", "full time", "new grad", "graduate"),
    ),
]


def _build_search_text(*parts: str) -> str:
    return re.sub(r"\s+", " ", " ".join(part for part in parts if part)).strip().lower()


def infer_position_type(*, title: str, location: str = "", raw_text: str = "", source_url: str = "") -> str:
    search_text = _build_search_text(title, location, raw_text, source_url)

    for position_type, keywords in POSITION_TYPE_KEYWORDS:
        if any(keyword in search_text for keyword in keywords):
            return position_type

    return Job.PositionType.UNKNOWN


def infer_position_type_for_job(job: Job) -> str:
    return infer_position_type(
        title=job.title,
        location=job.location,
        raw_text=job.raw_text,
        source_url=job.source_url or "",
    )
