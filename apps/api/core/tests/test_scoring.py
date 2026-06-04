from types import SimpleNamespace

from django.test import SimpleTestCase

from core.services.job_parser import parse_job_text
from core.services.profile_parser import parse_profile_text
from core.services.scoring import score_job_fit
from core.tests.fixtures import load_sample


class ScoringEngineTests(SimpleTestCase):
    def test_profile_parser_extracts_normalized_skills(self):
        skills = parse_profile_text(load_sample("sample_resume.txt"))
        assert skills == [
            "aws",
            "ci/cd",
            "django",
            "docker",
            "git",
            "github actions",
            "linux",
            "postgresql",
            "python",
            "react",
            "rest api",
            "typescript",
        ]

    def test_job_parser_splits_required_and_preferred_skills(self):
        parsed = parse_job_text(load_sample("sample_job_backend.txt"))
        assert parsed["requirements"] == [
            "aws",
            "django",
            "docker",
            "linux",
            "postgresql",
            "python",
            "rest api",
        ]
        assert parsed["preferred"] == [
            "distributed systems",
            "github actions",
            "kubernetes",
            "typescript",
        ]

    def test_scoring_engine_returns_deterministic_breakdown(self):
        profile = SimpleNamespace(
            normalized_skills=parse_profile_text(load_sample("sample_resume.txt"))
        )
        parsed_job = parse_job_text(load_sample("sample_job_backend.txt"))
        job = SimpleNamespace(
            normalized_requirements=parsed_job["requirements"],
            normalized_preferred=parsed_job["preferred"],
        )

        result = score_job_fit(profile=profile, job=job)

        assert result["match_score"] == 90
        assert result["recommendation"] == "HIGH_PRIORITY_APPLY"
        assert result["strengths"] == [
            "aws",
            "django",
            "docker",
            "linux",
            "postgresql",
            "python",
            "rest api",
            "github actions",
            "typescript",
        ]
        assert result["gaps"] == []
        assert result["missing_keywords"] == ["distributed systems", "kubernetes"]
        assert result["matched_skills_by_category"] == {
            "languages": ["python", "typescript"],
            "backend": ["django", "rest api"],
            "databases": ["postgresql"],
            "cloud": ["aws"],
            "devops": ["docker", "github actions"],
            "systems": ["linux"],
        }
        assert result["missing_skills_by_category"] == {
            "devops": ["kubernetes"],
            "systems": ["distributed systems"],
        }
        assert "High-priority apply" in result["reasoning"]
        assert result["score_breakdown"]["required_score"] == 70
        assert result["score_breakdown"]["preferred_score"] == 10
        assert result["score_breakdown"]["category_score"] == 10
