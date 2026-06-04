from unittest.mock import patch

from rest_framework.test import APITestCase

from core.models import CandidateProfile, GeneratedAnswer, Job, MatchReport
from core.tests.fixtures import load_sample


class PhaseZeroApiTests(APITestCase):
    def test_profile_get_returns_structured_404_when_missing(self):
        response = self.client.get("/api/v1/profile")

        assert response.status_code == 404
        assert response.data["error"]["code"] == "CANDIDATE_PROFILE_NOT_FOUND"

    def test_profile_post_upserts_singleton_profile(self):
        payload = {"resume_text": load_sample("sample_resume.txt")}

        first_response = self.client.post("/api/v1/profile", payload, format="json")
        second_response = self.client.post("/api/v1/profile", payload, format="json")

        assert first_response.status_code == 200
        assert second_response.status_code == 200
        assert CandidateProfile.objects.count() == 1
        assert first_response.data["normalized_skills"]

    def test_job_create_list_detail_and_analysis_flow(self):
        profile_response = self.client.post(
            "/api/v1/profile",
            {"resume_text": load_sample("sample_resume.txt")},
            format="json",
        )
        assert profile_response.status_code == 200

        create_job_response = self.client.post(
            "/api/v1/jobs",
            {
                "company_name": "Astranis",
                "title": "Backend Software Engineer Intern",
                "location": "San Francisco, CA",
                "raw_text": load_sample("sample_job_backend.txt"),
            },
            format="json",
        )
        assert create_job_response.status_code == 201
        job_id = create_job_response.data["id"]

        list_response = self.client.get("/api/v1/jobs")
        detail_response = self.client.get(f"/api/v1/jobs/{job_id}")
        analyze_response = self.client.post(f"/api/v1/jobs/{job_id}/analyze", {}, format="json")
        analysis_response = self.client.get(f"/api/v1/jobs/{job_id}/analysis")
        specific_analysis_response = self.client.get(
            f"/api/v1/jobs/{job_id}/analysis/{analyze_response.data['match_report_id']}"
        )

        assert list_response.status_code == 200
        assert len(list_response.data) == 1
        assert detail_response.status_code == 200
        assert analyze_response.status_code == 201
        assert analysis_response.status_code == 200
        assert specific_analysis_response.status_code == 200
        assert analyze_response.data["match_score"] == 90
        assert analyze_response.data["match_report_id"] == analyze_response.data["id"]
        assert analysis_response.data["match_report_id"] == analyze_response.data["match_report_id"]
        assert specific_analysis_response.data["match_report_id"] == analyze_response.data["match_report_id"]
        assert analysis_response.data["recommendation"] == "HIGH_PRIORITY_APPLY"
        assert "reasoning" in analysis_response.data
        assert "matched_skills_by_category" in analysis_response.data
        assert analysis_response.data["missing_skills_by_category"]["systems"] == [
            "distributed systems"
        ]
        assert Job.objects.count() == 1
        assert MatchReport.objects.count() == 1

    def test_analysis_keeps_history_and_latest_endpoint_returns_newest_report(self):
        self.client.post(
            "/api/v1/profile",
            {"resume_text": load_sample("sample_resume.txt")},
            format="json",
        )
        create_job_response = self.client.post(
            "/api/v1/jobs",
            {
                "company_name": "Astranis",
                "title": "Backend Software Engineer Intern",
                "location": "San Francisco, CA",
                "raw_text": load_sample("sample_job_backend.txt"),
            },
            format="json",
        )
        job_id = create_job_response.data["id"]

        first_analysis = self.client.post(f"/api/v1/jobs/{job_id}/analyze", {}, format="json")
        second_analysis = self.client.post(f"/api/v1/jobs/{job_id}/analyze", {}, format="json")
        latest_analysis = self.client.get(f"/api/v1/jobs/{job_id}/analysis")
        first_analysis_detail = self.client.get(
            f"/api/v1/jobs/{job_id}/analysis/{first_analysis.data['match_report_id']}"
        )

        assert first_analysis.status_code == 201
        assert second_analysis.status_code == 201
        assert latest_analysis.status_code == 200
        assert first_analysis_detail.status_code == 200
        assert first_analysis.data["match_report_id"] != second_analysis.data["match_report_id"]
        assert latest_analysis.data["match_report_id"] == second_analysis.data["match_report_id"]
        assert first_analysis_detail.data["match_report_id"] == first_analysis.data["match_report_id"]
        assert MatchReport.objects.count() == 2

    def test_latest_analysis_returns_structured_404_when_missing(self):
        job = Job.objects.create(
            company_name="Astranis",
            title="Backend Software Engineer Intern",
            location="San Francisco, CA",
            raw_text=load_sample("sample_job_backend.txt"),
            normalized_requirements=["python"],
            normalized_preferred=[],
        )

        response = self.client.get(f"/api/v1/jobs/{job.id}/analysis")

        assert response.status_code == 404
        assert response.data["error"]["code"] == "MATCH_REPORT_NOT_FOUND"

    def test_specific_analysis_returns_structured_404_when_missing(self):
        self.client.post(
            "/api/v1/profile",
            {"resume_text": load_sample("sample_resume.txt")},
            format="json",
        )
        job = Job.objects.create(
            company_name="Astranis",
            title="Backend Software Engineer Intern",
            location="San Francisco, CA",
            raw_text=load_sample("sample_job_backend.txt"),
            normalized_requirements=["python"],
            normalized_preferred=[],
        )

        response = self.client.get(
            f"/api/v1/jobs/{job.id}/analysis/00000000-0000-0000-0000-000000000000"
        )

        assert response.status_code == 404
        assert response.data["error"]["code"] == "MATCH_REPORT_NOT_FOUND"

    def test_analyze_requires_existing_profile(self):
        job = Job.objects.create(
            company_name="Astranis",
            title="Backend Software Engineer Intern",
            location="San Francisco, CA",
            raw_text=load_sample("sample_job_backend.txt"),
            normalized_requirements=["python"],
            normalized_preferred=[],
        )

        response = self.client.post(f"/api/v1/jobs/{job.id}/analyze", {}, format="json")

        assert response.status_code == 400
        assert response.data["error"]["code"] == "CANDIDATE_PROFILE_REQUIRED"
        assert response.data["error"]["message"] == "Candidate profile is required before analysis"


class GeneratedAnswerApiTests(APITestCase):
    def setUp(self):
        profile_response = self.client.post(
            "/api/v1/profile",
            {"resume_text": load_sample("sample_resume.txt")},
            format="json",
        )
        self.profile_id = profile_response.data["id"]
        create_job_response = self.client.post(
            "/api/v1/jobs",
            {
                "company_name": "Astranis",
                "title": "Backend Software Engineer Intern",
                "location": "San Francisco, CA",
                "raw_text": load_sample("sample_job_backend.txt"),
            },
            format="json",
        )
        self.job_id = create_job_response.data["id"]
        analysis_response = self.client.post(f"/api/v1/jobs/{self.job_id}/analyze", {}, format="json")
        self.match_report_id = analysis_response.data["match_report_id"]

    def test_generate_answer_creates_record_for_selected_match_report(self):
        response = self.client.post(
            f"/api/v1/jobs/{self.job_id}/answers/generate",
            {
                "answer_type": "WHY_ROLE",
                "match_report_id": self.match_report_id,
            },
            format="json",
        )

        assert response.status_code == 201
        assert response.data["job_id"] == self.job_id
        assert response.data["match_report_id"] == self.match_report_id
        assert response.data["answer_type"] == "WHY_ROLE"
        assert response.data["content"]
        assert response.data["evidence_summary"]
        assert response.data["generator_version"] == "phase1-local-v1"
        assert GeneratedAnswer.objects.count() == 1

    def test_generate_answer_upserts_same_job_match_report_and_answer_type(self):
        first_response = self.client.post(
            f"/api/v1/jobs/{self.job_id}/answers/generate",
            {
                "answer_type": "GOOD_FIT",
                "match_report_id": self.match_report_id,
            },
            format="json",
        )
        second_response = self.client.post(
            f"/api/v1/jobs/{self.job_id}/answers/generate",
            {
                "answer_type": "GOOD_FIT",
                "match_report_id": self.match_report_id,
            },
            format="json",
        )

        assert first_response.status_code == 201
        assert second_response.status_code == 200
        assert first_response.data["id"] == second_response.data["id"]
        assert GeneratedAnswer.objects.count() == 1

    def test_generate_answer_requires_matching_match_report(self):
        other_job = self.client.post(
            "/api/v1/jobs",
            {
                "company_name": "Other",
                "title": "Platform Intern",
                "location": "Remote",
                "raw_text": load_sample("sample_job_backend.txt"),
            },
            format="json",
        )

        response = self.client.post(
            f"/api/v1/jobs/{other_job.data['id']}/answers/generate",
            {
                "answer_type": "WHY_COMPANY",
                "match_report_id": self.match_report_id,
            },
            format="json",
        )

        assert response.status_code == 404
        assert response.data["error"]["code"] == "MATCH_REPORT_NOT_FOUND"

    def test_list_answers_returns_empty_array_before_generation(self):
        response = self.client.get(f"/api/v1/jobs/{self.job_id}/answers")

        assert response.status_code == 200
        assert response.data["job_id"] == self.job_id
        assert response.data["match_report_id"] == self.match_report_id
        assert response.data["answers"] == []

    def test_list_answers_returns_generated_answers_for_match_report(self):
        self.client.post(
            f"/api/v1/jobs/{self.job_id}/answers/generate",
            {
                "answer_type": "WHY_COMPANY",
                "match_report_id": self.match_report_id,
            },
            format="json",
        )
        self.client.post(
            f"/api/v1/jobs/{self.job_id}/answers/generate",
            {
                "answer_type": "SELF_INTRODUCTION",
                "match_report_id": self.match_report_id,
            },
            format="json",
        )

        response = self.client.get(f"/api/v1/jobs/{self.job_id}/answers?match_report_id={self.match_report_id}")

        assert response.status_code == 200
        assert len(response.data["answers"]) == 2
        assert {item["answer_type"] for item in response.data["answers"]} == {
            "WHY_COMPANY",
            "SELF_INTRODUCTION",
        }

    def test_generate_answer_uses_provider_abstraction(self):
        with patch("core.services.answer_generation.get_answer_provider") as mocked_provider_factory:
            mocked_provider = mocked_provider_factory.return_value
            mocked_provider.generate.return_value.content = "Custom provider output"
            mocked_provider.generate.return_value.evidence_summary = ["Resume references Django"]
            mocked_provider.generate.return_value.generator_version = "test-provider-v1"

            response = self.client.post(
                f"/api/v1/jobs/{self.job_id}/answers/generate",
                {
                    "answer_type": "WHY_ROLE",
                    "match_report_id": self.match_report_id,
                },
                format="json",
            )

        assert response.status_code == 201
        assert response.data["content"] == "Custom provider output"
        assert response.data["generator_version"] == "test-provider-v1"

    def test_generate_answer_returns_failure_when_validation_rejects_output(self):
        with patch("core.services.answer_generation.get_answer_provider") as mocked_provider_factory:
            mocked_provider = mocked_provider_factory.return_value
            mocked_provider.generate.return_value.content = "I improved performance by 300%."
            mocked_provider.generate.return_value.evidence_summary = ["Resume references Django"]
            mocked_provider.generate.return_value.generator_version = "test-provider-v1"

            response = self.client.post(
                f"/api/v1/jobs/{self.job_id}/answers/generate",
                {
                    "answer_type": "GOOD_FIT",
                    "match_report_id": self.match_report_id,
                },
                format="json",
            )

        assert response.status_code == 500
        assert response.data["error"]["code"] == "ANSWER_GENERATION_FAILED"
