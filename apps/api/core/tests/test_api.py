from rest_framework.test import APITestCase

from core.models import CandidateProfile, Job, MatchReport
from core.tests.fixtures import load_sample


class PhaseZeroApiTests(APITestCase):
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

        assert list_response.status_code == 200
        assert len(list_response.data) == 1
        assert detail_response.status_code == 200
        assert analyze_response.status_code == 201
        assert analysis_response.status_code == 200
        assert analyze_response.data["match_score"] == 90
        assert analysis_response.data["recommendation"] == "HIGH_PRIORITY_APPLY"
        assert "reasoning" in analysis_response.data
        assert "matched_skills_by_category" in analysis_response.data
        assert analysis_response.data["missing_skills_by_category"]["systems"] == [
            "distributed systems"
        ]
        assert Job.objects.count() == 1
        assert MatchReport.objects.count() == 1

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
        assert response.data["error"]["message"] == "Candidate profile is required before analysis"
