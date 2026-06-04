from datetime import date, timedelta
from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APITestCase

from core.models import CandidateProfile, GeneratedAnswer, Job, MatchReport, RecruitingPreferences
from core.services.job_ingestion import FetchedDocument
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
        assert create_job_response.data["source_type"] == "MANUAL"
        assert create_job_response.data["ingestion_status"] == "MANUAL"
        assert create_job_response.data["source_url"] is None
        assert create_job_response.data["external_id"] is None
        assert create_job_response.data["content_hash"] is None
        assert create_job_response.data["last_seen_at"] is None
        assert create_job_response.data["workflow_status"] == "SAVED"
        assert create_job_response.data["applied_date"] is None
        assert create_job_response.data["notes"] == ""
        assert create_job_response.data["next_action"] == ""
        assert create_job_response.data["next_action_due_date"] is None
        assert create_job_response.data["is_archived"] is False
        assert create_job_response.data["is_hidden"] is False
        assert create_job_response.data["is_saved"] is True
        assert create_job_response.data["relevance"] == "REVIEW"
        assert create_job_response.data["relevance_reasons"]
        assert create_job_response.data["relevance_flags"] == ["No target term match detected."]
        assert create_job_response.data["relevance_score"] == 35
        assert create_job_response.data["latest_match_score"] is None
        assert create_job_response.data["latest_recommendation"] is None
        assert create_job_response.data["latest_match_report_id"] is None
        assert create_job_response.data["latest_analysis_created_at"] is None
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
        assert Job.objects.get(id=job_id).source_type == Job.SourceType.MANUAL
        assert Job.objects.get(id=job_id).ingestion_status == Job.IngestionStatus.MANUAL
        assert Job.objects.get(id=job_id).workflow_status == Job.WorkflowStatus.SAVED
        assert Job.objects.get(id=job_id).relevance == Job.Relevance.RELEVANT

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


class RecruitingPreferencesApiTests(APITestCase):
    def test_preferences_get_creates_default_singleton(self):
        response = self.client.get("/api/v1/preferences/recruiting")

        assert response.status_code == 200
        assert response.data["target_terms"] == [
            "Fall 2026",
            "Winter 2027",
            "Spring 2027",
            "Summer 2027",
        ]
        assert response.data["role_types"] == [
            "Backend",
            "Full-stack",
            "Platform",
            "Infrastructure",
            "AI/ML",
        ]
        assert RecruitingPreferences.objects.count() == 1

    def test_preferences_post_upserts_and_recomputes_job_relevance(self):
        create_job_response = self.client.post(
            "/api/v1/jobs",
            {
                "company_name": "SecureCo",
                "title": "Security Clearance Intern",
                "location": "Onsite",
                "raw_text": "Summer 2027 backend internship. Security clearance required.",
            },
            format="json",
        )
        job_id = create_job_response.data["id"]

        response = self.client.post(
            "/api/v1/preferences/recruiting",
            {
                "target_terms": ["Summer 2027"],
                "role_types": ["Backend", "Systems", "Cloud"],
                "preferred_locations": ["Onsite"],
                "remote_preference": "ONSITE",
                "preferred_industries": [],
                "excluded_keywords": ["defense"],
                "minimum_match_score": 50,
                "include_sponsorship_required_roles": False,
                "include_clearance_required_roles": True,
            },
            format="json",
        )

        assert response.status_code == 200
        assert RecruitingPreferences.objects.count() == 1
        job = Job.objects.get(id=job_id)
        assert job.relevance == Job.Relevance.REVIEW
        assert job.relevance_reasons

    def test_jobs_endpoint_supports_relevance_filters_and_recently_added(self):
        Job.objects.create(
            company_name="Astranis",
            title="Backend Intern",
            location="Remote",
            raw_text="Summer 2027 backend internship remote",
            relevance=Job.Relevance.HIGHLY_RELEVANT,
            relevance_reasons=["Strong backend match."],
        )
        older_job = Job.objects.create(
            company_name="Older Co",
            title="Data Intern",
            location="Remote",
            raw_text="Spring 2027 data internship remote",
            relevance=Job.Relevance.NOT_RELEVANT,
            relevance_reasons=["Out of scope."],
        )
        Job.objects.filter(id=older_job.id).update(created_at=timezone.now() - timedelta(days=10))

        response = self.client.get(
            "/api/v1/jobs?view=all&relevance=HIGHLY_RELEVANT&recently_added=true&sort=newest_first"
        )

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["company_name"] == "Astranis"


class JobUrlIngestionApiTests(APITestCase):
    def test_ingest_url_creates_greenhouse_job(self):
        with patch("core.services.job_ingestion.fetch_url_document") as mocked_fetch:
            mocked_fetch.return_value = FetchedDocument(
                final_url="https://boards.greenhouse.io/orbitlabs/jobs/gh-12345",
                html=load_sample("greenhouse_job.html"),
            )

            response = self.client.post(
                "/api/v1/jobs/ingest-url",
                {"url": "https://boards.greenhouse.io/orbitlabs/jobs/gh-12345#fragment"},
                format="json",
            )

        assert response.status_code == 201
        assert response.data["company_name"] == "Orbit Labs"
        assert response.data["title"] == "Backend Software Engineer Intern"
        assert response.data["location"] == "San Francisco, CA"
        assert response.data["source_type"] == "GREENHOUSE"
        assert response.data["source_url"] == "https://boards.greenhouse.io/orbitlabs/jobs/gh-12345"
        assert response.data["external_id"] == "gh-12345"
        assert response.data["content_hash"]
        assert response.data["ingestion_status"] == "INGESTED"
        assert response.data["workflow_status"] == "DISCOVERED"
        assert response.data["is_saved"] is False
        assert "python" in response.data["normalized_requirements"]
        assert "aws" in response.data["normalized_preferred"]

    def test_ingest_url_creates_generic_job(self):
        with patch("core.services.job_ingestion.fetch_url_document") as mocked_fetch:
            mocked_fetch.return_value = FetchedDocument(
                final_url="https://careers.brightridge.dev/roles/data-engineering-intern",
                html=load_sample("generic_job.html"),
            )

            response = self.client.post(
                "/api/v1/jobs/ingest-url",
                {"url": "https://careers.brightridge.dev/roles/data-engineering-intern"},
                format="json",
            )

        assert response.status_code == 201
        assert response.data["source_type"] == "OTHER"
        assert response.data["company_name"] == "Bright Ridge"
        assert response.data["title"] == "Data Engineering Intern"
        assert response.data["location"] == "Austin, TX"
        assert "sql" in response.data["normalized_requirements"]
        assert "aws" in response.data["normalized_preferred"]

    def test_ingest_url_detects_lever_and_ashby_sources(self):
        fixtures = [
            (
                "https://jobs.lever.co/launchpoint/platform-engineering-intern",
                "lever_job.html",
                "LEVER",
                "Launch Point",
            ),
            (
                "https://jobs.ashbyhq.com/pine-ai/product-security-intern",
                "ashby_job.html",
                "ASHBY",
                "Pine AI",
            ),
        ]

        for url, fixture_name, source_type, company_name in fixtures:
            with self.subTest(url=url):
                with patch("core.services.job_ingestion.fetch_url_document") as mocked_fetch:
                    mocked_fetch.return_value = FetchedDocument(
                        final_url=url,
                        html=load_sample(fixture_name),
                    )

                    response = self.client.post("/api/v1/jobs/ingest-url", {"url": url}, format="json")

                assert response.status_code == 201
                assert response.data["source_type"] == source_type
                assert response.data["company_name"] == company_name

    def test_ingest_url_returns_existing_job_for_duplicate_source_url(self):
        existing_job = Job.objects.create(
            company_name="Orbit Labs",
            title="Backend Software Engineer Intern",
            location="San Francisco, CA",
            raw_text="Requirements\nPython",
            source_type=Job.SourceType.GREENHOUSE,
            source_url="https://boards.greenhouse.io/orbitlabs/jobs/gh-12345",
            external_id="gh-12345",
            content_hash="existing-hash",
            ingestion_status=Job.IngestionStatus.INGESTED,
            normalized_requirements=["python"],
            normalized_preferred=[],
        )

        with patch("core.services.job_ingestion.fetch_url_document") as mocked_fetch:
            response = self.client.post(
                "/api/v1/jobs/ingest-url",
                {"url": "https://boards.greenhouse.io/orbitlabs/jobs/gh-12345"},
                format="json",
            )

        assert response.status_code == 200
        assert response.data["id"] == str(existing_job.id)
        assert Job.objects.count() == 1
        mocked_fetch.assert_not_called()

    def test_ingest_url_returns_existing_job_for_duplicate_content_hash(self):
        with patch("core.services.job_ingestion.fetch_url_document") as mocked_fetch:
            mocked_fetch.return_value = FetchedDocument(
                final_url="https://careers.brightridge.dev/roles/data-engineering-intern",
                html=load_sample("generic_job.html"),
            )
            created_response = self.client.post(
                "/api/v1/jobs/ingest-url",
                {"url": "https://careers.brightridge.dev/roles/data-engineering-intern"},
                format="json",
            )

        with patch("core.services.job_ingestion.fetch_url_document") as mocked_fetch:
            mocked_fetch.return_value = FetchedDocument(
                final_url="https://jobs.example.com/listings/data-intern",
                html=load_sample("generic_job.html"),
            )
            duplicate_response = self.client.post(
                "/api/v1/jobs/ingest-url",
                {"url": "https://jobs.example.com/listings/data-intern"},
                format="json",
            )

        assert created_response.status_code == 201
        assert duplicate_response.status_code == 200
        assert duplicate_response.data["id"] == created_response.data["id"]
        assert Job.objects.count() == 1

    def test_ingest_url_returns_structured_invalid_url_error(self):
        response = self.client.post("/api/v1/jobs/ingest-url", {"url": "not-a-url"}, format="json")

        assert response.status_code == 400
        assert response.data["error"]["code"] == "INVALID_URL"

    def test_ingest_url_returns_fetch_error(self):
        with patch("core.services.job_ingestion.fetch_url_document") as mocked_fetch:
            from core.services.job_ingestion import JobIngestionError

            mocked_fetch.side_effect = JobIngestionError(
                "Failed to fetch the job posting URL.",
                code="JOB_FETCH_FAILED",
                status_code=502,
            )
            response = self.client.post(
                "/api/v1/jobs/ingest-url",
                {"url": "https://jobs.lever.co/launchpoint/platform-engineering-intern"},
                format="json",
            )

        assert response.status_code == 502
        assert response.data["error"]["code"] == "JOB_FETCH_FAILED"

    def test_ingest_url_returns_extraction_failed_error(self):
        html = """
        <html>
          <head><title>Unstructured Listing</title></head>
          <body><main class="job-posting"><p>Requirements</p><p>Python</p></main></body>
        </html>
        """

        with patch("core.services.job_ingestion.fetch_url_document") as mocked_fetch:
            mocked_fetch.return_value = FetchedDocument(
                final_url="https://jobs.example.com/listings/unstructured",
                html=html,
            )

            response = self.client.post(
                "/api/v1/jobs/ingest-url",
                {"url": "https://jobs.example.com/listings/unstructured"},
                format="json",
            )

        assert response.status_code == 422
        assert response.data["error"]["code"] == "JOB_EXTRACTION_FAILED"

    def test_ingest_url_returns_empty_extraction_error(self):
        with patch("core.services.job_ingestion.fetch_url_document") as mocked_fetch:
            mocked_fetch.return_value = FetchedDocument(
                final_url="https://jobs.example.com/listings/empty",
                html=load_sample("empty_job.html"),
            )

            response = self.client.post(
                "/api/v1/jobs/ingest-url",
                {"url": "https://jobs.example.com/listings/empty"},
                format="json",
            )

        assert response.status_code == 422
        assert response.data["error"]["code"] == "JOB_EXTRACTION_EMPTY"


class RecruitingDashboardApiTests(APITestCase):
    def setUp(self):
        self.manual_job = Job.objects.create(
            company_name="Astranis",
            title="Backend Intern",
            location="San Francisco, CA",
            raw_text=load_sample("sample_job_backend.txt"),
            source_type=Job.SourceType.MANUAL,
            ingestion_status=Job.IngestionStatus.MANUAL,
            workflow_status=Job.WorkflowStatus.SAVED,
            is_saved=True,
            normalized_requirements=["python"],
            normalized_preferred=[],
        )
        self.discovered_job = Job.objects.create(
            company_name="Orbit Labs",
            title="Platform Intern",
            location="Remote",
            raw_text=load_sample("sample_job_backend.txt"),
            source_type=Job.SourceType.GREENHOUSE,
            source_url="https://boards.greenhouse.io/orbitlabs/jobs/gh-12345",
            ingestion_status=Job.IngestionStatus.INGESTED,
            workflow_status=Job.WorkflowStatus.DISCOVERED,
            is_saved=False,
            normalized_requirements=["python"],
            normalized_preferred=[],
        )
        self.archived_job = Job.objects.create(
            company_name="Pine AI",
            title="Security Intern",
            location="New York, NY",
            raw_text=load_sample("sample_job_backend.txt"),
            source_type=Job.SourceType.ASHBY,
            ingestion_status=Job.IngestionStatus.INGESTED,
            workflow_status=Job.WorkflowStatus.REJECTED,
            is_saved=True,
            is_archived=True,
            normalized_requirements=["python"],
            normalized_preferred=[],
        )

        profile = CandidateProfile.objects.create(
            resume_text=load_sample("sample_resume.txt"),
            normalized_skills=["python", "django"],
        )
        MatchReport.objects.create(
            job=self.manual_job,
            candidate_profile=profile,
            match_score=90,
            recommendation="HIGH_PRIORITY_APPLY",
            strengths=["Strong backend fit"],
            gaps=[],
            missing_keywords=[],
            matched_skills_by_category={"languages": ["python"]},
            missing_skills_by_category={},
            reasoning="Good fit",
            score_breakdown={"total": 90},
        )
        MatchReport.objects.create(
            job=self.discovered_job,
            candidate_profile=profile,
            match_score=65,
            recommendation="REVIEW",
            strengths=["Relevant experience"],
            gaps=["distributed systems"],
            missing_keywords=["distributed systems"],
            matched_skills_by_category={"languages": ["python"]},
            missing_skills_by_category={"systems": ["distributed systems"]},
            reasoning="Needs review",
            score_breakdown={"total": 65},
        )

    def test_jobs_list_returns_latest_match_summary_fields(self):
        response = self.client.get("/api/v1/jobs")

        assert response.status_code == 200
        assert len(response.data) == 2
        manual_job = next(item for item in response.data if item["id"] == str(self.manual_job.id))
        assert manual_job["latest_match_score"] == 90
        assert manual_job["latest_recommendation"] == "HIGH_PRIORITY_APPLY"
        assert manual_job["latest_match_report_id"] is not None
        assert manual_job["latest_analysis_created_at"] is not None

    def test_jobs_list_filters_by_status(self):
        response = self.client.get("/api/v1/jobs?status=DISCOVERED")

        assert response.status_code == 200
        assert [item["id"] for item in response.data] == [str(self.discovered_job.id)]

    def test_jobs_list_hides_archived_by_default_and_can_include_them(self):
        default_response = self.client.get("/api/v1/jobs")
        archived_response = self.client.get("/api/v1/jobs?include_archived=true")

        assert default_response.status_code == 200
        assert str(self.archived_job.id) not in {item["id"] for item in default_response.data}
        assert archived_response.status_code == 200
        assert str(self.archived_job.id) in {item["id"] for item in archived_response.data}

    def test_jobs_list_sorts_by_match_score_desc_by_default(self):
        response = self.client.get("/api/v1/jobs")

        assert response.status_code == 200
        assert [item["id"] for item in response.data] == [
            str(self.manual_job.id),
            str(self.discovered_job.id),
        ]

    def test_jobs_list_sorts_by_match_score_asc(self):
        response = self.client.get("/api/v1/jobs?sort=match_score_asc")

        assert response.status_code == 200
        assert [item["id"] for item in response.data] == [
            str(self.discovered_job.id),
            str(self.manual_job.id),
        ]

    def test_patch_job_updates_recruiting_fields(self):
        response = self.client.patch(
            f"/api/v1/jobs/{self.discovered_job.id}",
            {
                "workflow_status": "INTERVIEW",
                "notes": "Recruiter screen went well.",
                "next_action": "Prepare for technical interview",
                "next_action_due_date": "2026-06-10",
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data["workflow_status"] == "INTERVIEW"
        assert response.data["notes"] == "Recruiter screen went well."
        assert response.data["next_action"] == "Prepare for technical interview"
        assert response.data["next_action_due_date"] == "2026-06-10"
        assert response.data["is_saved"] is True

    def test_patch_job_sets_applied_date_when_marked_applied(self):
        response = self.client.patch(
            f"/api/v1/jobs/{self.discovered_job.id}",
            {"workflow_status": "APPLIED"},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["workflow_status"] == "APPLIED"
        assert response.data["applied_date"] == date.today().isoformat()

    def test_patch_job_can_archive_record(self):
        response = self.client.patch(
            f"/api/v1/jobs/{self.manual_job.id}",
            {"is_archived": True},
            format="json",
        )

        assert response.status_code == 200
        assert response.data["is_archived"] is True
