from dataclasses import dataclass

from core.models import CandidateProfile, GeneratedAnswer, Job, MatchReport


GENERATOR_VERSION = "phase1-local-v1"


@dataclass
class ProviderAnswerResult:
    content: str
    evidence_summary: list[str]
    generator_version: str = GENERATOR_VERSION


class AnswerProvider:
    def generate(
        self,
        *,
        candidate_profile: CandidateProfile,
        job: Job,
        match_report: MatchReport,
        answer_type: str,
    ) -> ProviderAnswerResult:
        raise NotImplementedError


class DeterministicLocalAnswerProvider(AnswerProvider):
    def generate(
        self,
        *,
        candidate_profile: CandidateProfile,
        job: Job,
        match_report: MatchReport,
        answer_type: str,
    ) -> ProviderAnswerResult:
        strengths = match_report.strengths[:3]
        preferred_matches = [
            skill for skill in job.normalized_preferred if skill in candidate_profile.normalized_skills
        ][:2]
        missing_keywords = match_report.missing_keywords[:2]
        project_lines = _extract_project_lines(candidate_profile.resume_text)
        candidate_name = _extract_candidate_name(candidate_profile.resume_text)

        if answer_type == GeneratedAnswer.AnswerType.WHY_COMPANY:
            role_focus = _join_phrases(job.normalized_requirements[:3])
            evidence = [
                f"Job is for {job.company_name} as a {job.title}",
                f"Posting emphasizes {role_focus}",
                f"Resume shows overlap in { _join_phrases(strengths) }",
            ]
            content = (
                f"I'm excited about {job.company_name} because this {job.title} role is centered on "
                f"{role_focus}, which lines up well with the backend work and tooling already reflected in my resume. "
                f"I'm especially motivated by the chance to contribute in an environment where { _join_phrases(strengths) } "
                f"are directly relevant from day one."
            )
        elif answer_type == GeneratedAnswer.AnswerType.WHY_ROLE:
            evidence = [
                f"Job requires { _join_phrases(job.normalized_requirements[:4]) }",
                f"Match report strengths include { _join_phrases(strengths) }",
                project_lines[0] if project_lines else "Resume includes backend project experience",
            ]
            content = (
                f"I'm drawn to this role because it focuses on the kind of backend engineering work I want to keep growing in, "
                f"especially around { _join_phrases(job.normalized_requirements[:3]) }. "
                f"My background already includes hands-on work with { _join_phrases(strengths) }, and this role feels like a strong next step "
                f"to deepen that experience in a production setting."
            )
        elif answer_type == GeneratedAnswer.AnswerType.GOOD_FIT:
            supporting_skills = preferred_matches or strengths
            evidence = [
                f"Match score is {match_report.match_score}",
                f"Recommendation is {match_report.recommendation}",
                f"Matched skills include { _join_phrases(supporting_skills[:4]) }",
            ]
            gap_sentence = (
                f" While there are still areas I would continue learning, such as { _join_phrases(missing_keywords) },"
                if missing_keywords
                else ""
            )
            content = (
                f"I'm a strong fit for this role because my experience already overlaps with many of the core skills the posting emphasizes, "
                f"including { _join_phrases(supporting_skills[:4]) }. The current analysis also highlights that alignment through a "
                f"{match_report.match_score} match score and a {match_report.recommendation.replace('_', ' ').lower()} recommendation."
                f"{gap_sentence} I would be able to contribute quickly while continuing to build depth."
            )
        elif answer_type == GeneratedAnswer.AnswerType.SELF_INTRODUCTION:
            evidence = [
                f"Candidate name is {candidate_name}",
                f"Resume lists skills in { _join_phrases(candidate_profile.normalized_skills[:5]) }",
                f"Relevant role is {job.title}",
            ]
            content = (
                f"I'm {candidate_name}, a software engineering candidate with experience across "
                f"{ _join_phrases(candidate_profile.normalized_skills[:5]) }. "
                f"I've built projects involving { _join_phrases(strengths) }, and I'm especially interested in opportunities like this "
                f"{job.title} role where I can contribute to backend systems while continuing to grow as an engineer."
            )
        else:
            accomplishment = project_lines[0] if project_lines else "Built backend and full-stack projects reflected in my resume."
            evidence = [
                accomplishment,
                f"Resume skills include { _join_phrases(strengths or candidate_profile.normalized_skills[:3]) }",
                "No unsupported metrics were added",
            ]
            content = (
                f"One accomplishment I'm especially proud of is that I { _normalize_project_line(accomplishment) } "
                f"That work stands out to me because it brought together { _join_phrases(strengths or candidate_profile.normalized_skills[:3]) } "
                f"and showed that I can take a project from implementation through deployment-oriented concerns in a practical way."
            )

        return ProviderAnswerResult(
            content=" ".join(content.split()),
            evidence_summary=[" ".join(item.split()) for item in evidence if item.strip()],
        )


def get_answer_provider() -> AnswerProvider:
    return DeterministicLocalAnswerProvider()


def _extract_candidate_name(resume_text: str) -> str:
    first_line = next((line.strip() for line in resume_text.splitlines() if line.strip()), "The candidate")
    return first_line


def _extract_project_lines(resume_text: str) -> list[str]:
    project_lines: list[str] = []
    in_projects_section = False

    for raw_line in resume_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.lower() == "projects":
            in_projects_section = True
            continue
        if in_projects_section and not line.startswith("- "):
            break
        if in_projects_section and line.startswith("- "):
            project_lines.append(line.lstrip("-").strip())

    return project_lines


def _join_phrases(items: list[str]) -> str:
    cleaned = [item for item in items if item]
    if not cleaned:
        return "relevant technical work"
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} and {cleaned[1]}"
    return f"{', '.join(cleaned[:-1])}, and {cleaned[-1]}"


def _normalize_project_line(project_line: str) -> str:
    return project_line[0].lower() + project_line[1:] if project_line else project_line
