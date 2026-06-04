from django.test import TestCase

from core.models import Job, RecruitingPreferences
from core.services.relevance import evaluate_job_relevance


class RelevanceEngineTests(TestCase):
    def setUp(self):
        self.preferences = RecruitingPreferences.objects.create(
            target_terms=["Summer 2027"],
            role_types=["Backend", "Platform", "Systems", "Cloud"],
            position_types=[Job.PositionType.INTERN],
            preferred_locations=["San Francisco"],
            remote_preference=RecruitingPreferences.RemotePreference.ANY,
            preferred_industries=["space"],
            excluded_keywords=["clearance"],
            minimum_match_score=60,
            include_sponsorship_required_roles=False,
            include_clearance_required_roles=False,
        )

    def test_highly_relevant_backend_role_with_matching_score(self):
        job = Job(
            company_name="Orbit Labs",
            title="Backend Platform Intern",
            location="San Francisco, CA",
            raw_text="Summer 2027 space infrastructure internship with backend APIs on AWS.",
            normalized_requirements=["python", "aws"],
            normalized_preferred=["distributed systems"],
        )

        result = evaluate_job_relevance(job, preferences=self.preferences, latest_match_score=88)

        assert result.classification == Job.Relevance.HIGHLY_RELEVANT
        assert result.score >= 80
        assert result.reasons

    def test_missing_analysis_caps_role_at_review_when_signals_are_mixed(self):
        job = Job(
            company_name="Launch Point",
            title="Platform Systems Intern",
            location="Austin, TX",
            raw_text="Summer 2027 platform systems internship.",
            normalized_requirements=[],
            normalized_preferred=[],
        )

        result = evaluate_job_relevance(job, preferences=self.preferences, latest_match_score=None)

        assert result.classification == Job.Relevance.REVIEW
        assert "No match analysis yet" in result.reasons[0]

    def test_excluded_keyword_forces_not_relevant(self):
        job = Job(
            company_name="DefenseCo",
            title="Cloud Systems Intern",
            location="San Francisco, CA",
            raw_text="Summer 2027 cloud internship. Clearance required.",
            normalized_requirements=["aws"],
            normalized_preferred=[],
        )

        result = evaluate_job_relevance(job, preferences=self.preferences, latest_match_score=92)

        assert result.classification == Job.Relevance.NOT_RELEVANT
        assert any("clearance" in flag.lower() for flag in result.flags)

    def test_mismatched_position_type_adds_flag(self):
        job = Job(
            company_name="Northstar",
            title="New Grad Software Engineer",
            location="Remote",
            raw_text="Summer 2027 full-time graduate software engineer role.",
            normalized_requirements=["python"],
            normalized_preferred=[],
        )

        result = evaluate_job_relevance(job, preferences=self.preferences, latest_match_score=88)

        assert result.classification == Job.Relevance.NOT_RELEVANT
        assert any("position does not match" in flag.lower() for flag in result.flags)
