from __future__ import annotations

from core.models import CandidateProfile, Job, MatchReport
from core.services.taxonomy import CATEGORY_ORDER, group_skills_by_category


def _round_score(value: float) -> int:
    return max(0, min(100, round(value)))


def _recommendation_for_score(score: int) -> str:
    if score >= 80:
        return MatchReport.Recommendation.HIGH_PRIORITY_APPLY
    if score >= 60:
        return MatchReport.Recommendation.APPLY
    if score >= 40:
        return MatchReport.Recommendation.REVIEW
    return MatchReport.Recommendation.LOW_PRIORITY


def _coverage_ratio(matched: list[str], total: set[str]) -> float:
    if not total:
        return 1.0
    return len(matched) / len(total)


def _build_reasoning(
    recommendation: str,
    score: int,
    matched_required: list[str],
    required_skills: set[str],
    matched_preferred: list[str],
    preferred_skills: set[str],
    matched_by_category: dict[str, list[str]],
    missing_by_category: dict[str, list[str]],
) -> str:
    required_coverage = _coverage_ratio(matched_required, required_skills)
    preferred_coverage = _coverage_ratio(matched_preferred, preferred_skills)
    covered_categories = list(matched_by_category.keys())
    missing_categories = list(missing_by_category.keys())

    recommendation_labels = {
        MatchReport.Recommendation.HIGH_PRIORITY_APPLY: "High-priority apply",
        MatchReport.Recommendation.APPLY: "Apply",
        MatchReport.Recommendation.REVIEW: "Review",
        MatchReport.Recommendation.LOW_PRIORITY: "Low priority",
    }

    reasons = [
        (
            f"{recommendation_labels[recommendation]} because the profile matches "
            f"{len(matched_required)}/{len(required_skills) or 0} required skills "
            f"({round(required_coverage * 100)}%) for a score of {score}."
        )
    ]

    if covered_categories:
        reasons.append(f"Strongest coverage appears in {', '.join(covered_categories)}.")

    if preferred_skills:
        reasons.append(
            f"Preferred-skill coverage is {len(matched_preferred)}/{len(preferred_skills)} "
            f"({round(preferred_coverage * 100)}%)."
        )

    if missing_categories:
        reasons.append(f"Main gaps remain in {', '.join(missing_categories)}.")
    elif required_skills:
        reasons.append("There are no missing required-skill categories in the current taxonomy match.")

    return " ".join(reasons)


def score_job_fit(profile: CandidateProfile, job: Job) -> dict[str, object]:
    profile_skills = set(profile.normalized_skills)
    required_skills = set(job.normalized_requirements)
    preferred_skills = set(job.normalized_preferred)

    matched_required = sorted(required_skills & profile_skills)
    missing_required = sorted(required_skills - profile_skills)
    matched_preferred = sorted(preferred_skills & profile_skills)
    missing_preferred = sorted(preferred_skills - profile_skills)

    required_categories = {
        category for category in group_skills_by_category(list(required_skills)).keys()
    }
    matched_required_categories = {
        category for category in group_skills_by_category(matched_required).keys()
    }

    required_score = 0.0
    preferred_score = 0.0
    category_score = 0.0

    if required_skills:
        required_score = _coverage_ratio(matched_required, required_skills) * 70
    if preferred_skills:
        preferred_score = (len(matched_preferred) / len(preferred_skills)) * 20
    if required_categories:
        category_score = (len(matched_required_categories) / len(required_categories)) * 10
    elif not required_skills:
        required_score = 100.0
    else:
        category_score = 10.0

    match_score = _round_score(required_score + preferred_score + category_score)
    strengths = matched_required + [skill for skill in matched_preferred if skill not in matched_required]
    gaps = missing_required
    missing_keywords = missing_required + [
        skill for skill in missing_preferred if skill not in missing_required
    ]
    matched_skills_by_category = group_skills_by_category(strengths)
    missing_skills_by_category = group_skills_by_category(missing_keywords)
    recommendation = _recommendation_for_score(match_score)
    reasoning = _build_reasoning(
        recommendation=recommendation,
        score=match_score,
        matched_required=matched_required,
        required_skills=required_skills,
        matched_preferred=matched_preferred,
        preferred_skills=preferred_skills,
        matched_by_category=matched_skills_by_category,
        missing_by_category=missing_skills_by_category,
    )

    return {
        "match_score": match_score,
        "recommendation": recommendation,
        "strengths": strengths,
        "gaps": gaps,
        "missing_keywords": missing_keywords,
        "matched_skills_by_category": matched_skills_by_category,
        "missing_skills_by_category": missing_skills_by_category,
        "reasoning": reasoning,
        "score_breakdown": {
            "profile_skills": sorted(profile_skills),
            "required_skills": sorted(required_skills),
            "preferred_skills": sorted(preferred_skills),
            "matched_required": matched_required,
            "matched_preferred": matched_preferred,
            "missing_required": missing_required,
            "missing_preferred": missing_preferred,
            "required_categories": sorted(required_categories, key=CATEGORY_ORDER.index),
            "matched_required_categories": sorted(
                matched_required_categories,
                key=CATEGORY_ORDER.index,
            ),
            "required_score": _round_score(required_score),
            "preferred_score": _round_score(preferred_score),
            "category_score": _round_score(category_score),
        },
    }
