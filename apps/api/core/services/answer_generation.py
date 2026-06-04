from dataclasses import dataclass

from core.models import GeneratedAnswer, Job, MatchReport
from core.services.answer_validation import validate_generated_answer
from core.services.llm_provider import get_answer_provider


@dataclass
class GeneratedAnswerResult:
    answer: GeneratedAnswer
    created: bool


def generate_answer_for_match_report(
    *,
    job: Job,
    match_report: MatchReport,
    answer_type: str,
) -> GeneratedAnswerResult:
    provider = get_answer_provider()
    provider_result = provider.generate(
        candidate_profile=match_report.candidate_profile,
        job=job,
        match_report=match_report,
        answer_type=answer_type,
    )

    validated = validate_generated_answer(
        content=provider_result.content,
        evidence_summary=provider_result.evidence_summary,
        source_texts=[
            match_report.candidate_profile.resume_text,
            job.raw_text,
            match_report.reasoning,
            str(match_report.match_score),
            match_report.recommendation,
        ],
    )

    answer, created = GeneratedAnswer.objects.update_or_create(
        job=job,
        match_report=match_report,
        answer_type=answer_type,
        defaults={
            "candidate_profile": match_report.candidate_profile,
            "content": validated.content,
            "evidence_summary": validated.evidence_summary,
            "generator_version": provider_result.generator_version,
        },
    )
    return GeneratedAnswerResult(answer=answer, created=created)
