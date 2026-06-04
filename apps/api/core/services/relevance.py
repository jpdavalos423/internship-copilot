from __future__ import annotations

from dataclasses import dataclass

from django.utils import timezone

from core.models import Job, MatchReport, RecruitingPreferences

DEFAULT_TARGET_TERMS = [
    "Fall 2026",
    "Winter 2027",
    "Spring 2027",
    "Summer 2027",
]

DEFAULT_ROLE_TYPES = [
    "Backend",
    "Full-stack",
    "Platform",
    "Infrastructure",
    "AI/ML",
]

ROLE_TYPE_KEYWORDS = {
    "Backend": ["backend", "back-end", "api", "server"],
    "Frontend": ["frontend", "front-end", "ui", "web"],
    "Full-stack": ["full stack", "full-stack", "fullstack"],
    "Platform": ["platform", "internal platform", "developer platform"],
    "Infrastructure": ["infrastructure", "infra", "sre", "reliability"],
    "AI/ML": ["ai", "ml", "machine learning", "deep learning"],
    "Data": ["data", "analytics", "data engineering"],
    "Mobile": ["mobile", "ios", "android", "react native"],
    "Systems": ["systems", "embedded", "operating systems", "distributed systems"],
    "Developer Tools": ["developer tools", "devtools", "tooling", "build systems", "cli"],
    "Cloud": ["cloud", "aws", "gcp", "azure", "distributed infrastructure"],
}

REMOTE_KEYWORDS = ["remote", "work from home", "distributed team"]
HYBRID_KEYWORDS = ["hybrid"]
ONSITE_KEYWORDS = ["onsite", "on-site", "in office", "in-office"]
SPONSORSHIP_KEYWORDS = [
    "visa sponsorship",
    "sponsorship",
    "require sponsorship",
    "requires sponsorship",
    "work authorization",
    "authorized to work",
]
CLEARANCE_KEYWORDS = [
    "security clearance",
    "secret clearance",
    "top secret",
    "ts/sci",
    "clearance required",
]


@dataclass
class RelevanceEvaluation:
    classification: str
    score: int
    reasons: list[str]
    flags: list[str]


def get_default_preferences_payload() -> dict[str, object]:
    return {
        "target_terms": DEFAULT_TARGET_TERMS,
        "role_types": DEFAULT_ROLE_TYPES,
        "preferred_locations": [],
        "remote_preference": RecruitingPreferences.RemotePreference.ANY,
        "preferred_industries": [],
        "excluded_keywords": [],
        "minimum_match_score": 60,
        "include_sponsorship_required_roles": False,
        "include_clearance_required_roles": False,
    }


def get_or_create_preferences() -> RecruitingPreferences:
    preferences = RecruitingPreferences.objects.order_by("-updated_at").first()
    if preferences is not None:
        return preferences
    return RecruitingPreferences.objects.create(**get_default_preferences_payload())


def _normalize(value: str) -> str:
    return value.strip().lower()


def _contains_any(text: str, terms: list[str]) -> list[str]:
    normalized_text = _normalize(text)
    return [term for term in terms if _normalize(term) in normalized_text]


def _latest_match_score(job: Job) -> int | None:
    report = job.match_reports.order_by("-created_at").only("match_score").first()
    if report is None:
        return None
    return int(report.match_score)


def _build_search_text(job: Job) -> str:
    source_text = job.source_url or ""
    return " ".join(
        [
            job.title,
            job.location,
            job.raw_text,
            source_text,
            " ".join(job.normalized_requirements),
            " ".join(job.normalized_preferred),
        ]
    ).lower()


def _role_type_matches(search_text: str, selected_role_types: list[str]) -> list[str]:
    matches: list[str] = []
    for role_type in selected_role_types:
        keywords = ROLE_TYPE_KEYWORDS.get(role_type, [])
        if any(keyword in search_text for keyword in keywords):
            matches.append(role_type)
    return matches


def _location_matches(job: Job, preferences: RecruitingPreferences) -> tuple[bool, bool]:
    search_text = _build_search_text(job)
    location_match = False
    if preferences.preferred_locations:
        location_match = any(
            _normalize(location) in search_text for location in preferences.preferred_locations
        )

    remote_pref = preferences.remote_preference
    if remote_pref == RecruitingPreferences.RemotePreference.ANY:
        return location_match or not preferences.preferred_locations, False

    if remote_pref == RecruitingPreferences.RemotePreference.REMOTE:
        return any(keyword in search_text for keyword in REMOTE_KEYWORDS), True

    if remote_pref == RecruitingPreferences.RemotePreference.HYBRID:
        return any(keyword in search_text for keyword in HYBRID_KEYWORDS), True

    return any(keyword in search_text for keyword in ONSITE_KEYWORDS), True


def _classify(score: int, match_score: int | None, hard_blocked: bool) -> str:
    if hard_blocked or score < 35:
        return Job.Relevance.NOT_RELEVANT
    if score >= 80 and match_score is not None:
        return Job.Relevance.HIGHLY_RELEVANT
    if score >= 60:
        return Job.Relevance.RELEVANT
    return Job.Relevance.REVIEW


def evaluate_job_relevance(
    job: Job,
    *,
    preferences: RecruitingPreferences | None = None,
    latest_match_score: int | None = None,
) -> RelevanceEvaluation:
    preferences = preferences or get_or_create_preferences()
    match_score = latest_match_score if latest_match_score is not None else _latest_match_score(job)
    search_text = _build_search_text(job)

    score = 0
    reasons: list[str] = []
    flags: list[str] = []

    if match_score is not None:
        normalized_match = min(match_score, 100)
        score += round(normalized_match * 0.4)
        if match_score >= preferences.minimum_match_score:
            reasons.append(f"Match score {match_score} clears your {preferences.minimum_match_score} threshold.")
        else:
            reasons.append(
                f"Match score {match_score} is below your {preferences.minimum_match_score} threshold."
            )
    else:
        reasons.append("No match analysis yet, so relevance is based on role and preference signals.")

    matched_role_types = _role_type_matches(search_text, list(preferences.role_types))
    role_points = 25 if matched_role_types else 0
    score += role_points
    if matched_role_types:
        reasons.append(f"Role alignment: {', '.join(matched_role_types[:3])}.")
    else:
        flags.append("No preferred role-type match detected.")

    matched_target_terms = _contains_any(search_text, list(preferences.target_terms))
    if matched_target_terms:
        score += 15
        reasons.append(f"Target term match: {matched_target_terms[0]}.")

    location_match, remote_specific = _location_matches(job, preferences)
    if location_match:
        score += 10
        if remote_specific:
            reasons.append(f"{preferences.remote_preference.title()} preference matches this role.")
        elif preferences.preferred_locations:
            reasons.append("Location aligns with your preferred locations.")
    elif preferences.preferred_locations or remote_specific:
        flags.append("Location or remote setup does not match your preferences.")

    matched_industries = _contains_any(search_text, list(preferences.preferred_industries))
    if matched_industries:
        score += 10
        reasons.append(f"Industry signal: {matched_industries[0]}.")

    hard_blocked = False

    matched_excluded_keywords = _contains_any(search_text, list(preferences.excluded_keywords))
    for keyword in matched_excluded_keywords:
        flags.append(f"Contains excluded keyword: {keyword}.")
    if matched_excluded_keywords:
        score -= 45
        hard_blocked = True

    has_sponsorship_requirement = bool(_contains_any(search_text, SPONSORSHIP_KEYWORDS))
    if has_sponsorship_requirement and not preferences.include_sponsorship_required_roles:
        flags.append("Role appears to require sponsorship.")
        score -= 35
        hard_blocked = True

    has_clearance_requirement = bool(_contains_any(search_text, CLEARANCE_KEYWORDS))
    if has_clearance_requirement and not preferences.include_clearance_required_roles:
        flags.append("Role appears to require clearance.")
        score -= 35
        hard_blocked = True

    if match_score is not None and match_score < preferences.minimum_match_score:
        score -= 15

    if not matched_target_terms and preferences.target_terms:
        flags.append("No target term match detected.")

    if not reasons:
        reasons.append("This role is visible for manual review based on limited preference signals.")

    score = max(0, min(100, score))
    classification = _classify(score, match_score, hard_blocked)

    if match_score is None and classification == Job.Relevance.HIGHLY_RELEVANT:
        classification = Job.Relevance.REVIEW

    visible_reasons = reasons[:3]
    if not visible_reasons:
        visible_reasons = ["This role needs manual review."]

    return RelevanceEvaluation(
        classification=classification,
        score=score,
        reasons=visible_reasons,
        flags=flags[:5],
    )


def refresh_job_relevance(
    job: Job,
    *,
    preferences: RecruitingPreferences | None = None,
    latest_match_score: int | None = None,
) -> RelevanceEvaluation:
    evaluation = evaluate_job_relevance(
        job,
        preferences=preferences,
        latest_match_score=latest_match_score,
    )
    job.relevance = evaluation.classification
    job.relevance_reasons = evaluation.reasons
    job.relevance_flags = evaluation.flags
    job.relevance_last_evaluated_at = timezone.now()
    job.save(
        update_fields=[
            "relevance",
            "relevance_reasons",
            "relevance_flags",
            "relevance_last_evaluated_at",
            "updated_at",
        ]
    )
    return evaluation


def refresh_all_job_relevance(*, preferences: RecruitingPreferences | None = None) -> None:
    preferences = preferences or get_or_create_preferences()
    latest_report_lookup: dict[object, int] = {}
    for report in MatchReport.objects.order_by("job_id", "-created_at").values("job_id", "match_score"):
        latest_report_lookup.setdefault(report["job_id"], report["match_score"])
    for job in Job.objects.all():
        refresh_job_relevance(
            job,
            preferences=preferences,
            latest_match_score=latest_report_lookup.get(job.id),
        )
