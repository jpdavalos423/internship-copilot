import json
from datetime import timedelta
from unittest.mock import patch

from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APITestCase

from core.models import Job, JobSource
from core.services.job_discovery import (
    fetch_source_listings,
    is_target_listing,
    normalize_source_base_url,
    scan_all_sources,
)
from core.services.job_ingestion import FetchedDocument
from core.tests.fixtures import load_sample


class JobDiscoveryServiceTests(APITestCase):
    def test_normalize_source_base_url_supports_all_provider_patterns(self):
        fixtures = [
            (
                "https://boards.greenhouse.io/orbitlabs/jobs",
                JobSource.SourceType.GREENHOUSE,
                "https://boards.greenhouse.io/orbitlabs",
            ),
            (
                "https://jobs.lever.co/launchpoint/",
                JobSource.SourceType.LEVER,
                "https://jobs.lever.co/launchpoint",
            ),
            (
                "https://jobs.ashbyhq.com/Pine-AI",
                JobSource.SourceType.ASHBY,
                "https://jobs.ashbyhq.com/Pine-AI",
            ),
        ]

        for url, source_type, normalized in fixtures:
            with self.subTest(url=url):
                detected_type, normalized_url = normalize_source_base_url(url, source_type)
                assert detected_type == source_type
                assert normalized_url == normalized

    def test_target_listing_filter_prefers_internships_and_rejects_obvious_non_targets(self):
        from core.services.job_discovery import DiscoveredListing

        assert is_target_listing(
            DiscoveredListing(
                url="https://jobs.example.com/platform-intern",
                title="Platform Engineering Intern",
                location="Remote",
                source_type=JobSource.SourceType.LEVER,
            )
        )
        assert not is_target_listing(
            DiscoveredListing(
                url="https://jobs.example.com/sales-manager",
                title="Senior Sales Manager",
                location="New York, NY",
                source_type=JobSource.SourceType.LEVER,
            )
        )

    def test_fetch_source_listings_parses_greenhouse_lever_and_ashby_fixtures(self):
        sources = [
            JobSource(
                name="Orbit",
                company_name="Orbit Labs",
                source_type=JobSource.SourceType.GREENHOUSE,
                base_url="https://boards.greenhouse.io/orbitlabs",
            ),
            JobSource(
                name="Launch Point",
                company_name="Launch Point",
                source_type=JobSource.SourceType.LEVER,
                base_url="https://jobs.lever.co/launchpoint",
            ),
            JobSource(
                name="Pine AI",
                company_name="Pine AI",
                source_type=JobSource.SourceType.ASHBY,
                base_url="https://jobs.ashbyhq.com/pine-ai",
            ),
        ]

        responses = {
            "https://boards-api.greenhouse.io/v1/boards/orbitlabs/jobs": json.loads(
                load_sample("greenhouse_board.json")
            ),
            "https://api.lever.co/v0/postings/launchpoint?mode=json&skip=0&limit=50": json.loads(
                load_sample("lever_board_page_1.json")
            ),
            "https://api.ashbyhq.com/posting-api/job-board/pine-ai": json.loads(
                load_sample("ashby_board.json")
            ),
        }

        with patch("core.services.job_discovery.fetch_json_document") as mocked_fetch:
            mocked_fetch.side_effect = lambda url: responses[url]

            greenhouse_listings = fetch_source_listings(sources[0])
            lever_listings = fetch_source_listings(sources[1])
            ashby_listings = fetch_source_listings(sources[2])

        assert len(greenhouse_listings) == 1
        assert greenhouse_listings[0].url == "https://boards.greenhouse.io/orbitlabs/jobs/gh-12345"
        assert len(lever_listings) == 2
        assert lever_listings[0].url == "https://jobs.lever.co/launchpoint/platform-engineering-intern"
        assert len(ashby_listings) == 1
        assert ashby_listings[0].url == "https://jobs.ashbyhq.com/pine-ai/product-security-intern"

    def test_scan_all_sources_due_only_respects_last_scanned_at(self):
        due_source = JobSource.objects.create(
            name="Orbit",
            company_name="Orbit Labs",
            source_type=JobSource.SourceType.GREENHOUSE,
            base_url="https://boards.greenhouse.io/orbitlabs",
            last_scanned_at=timezone.now() - timedelta(hours=30),
            scan_interval_hours=24,
        )
        not_due_source = JobSource.objects.create(
            name="Launch Point",
            company_name="Launch Point",
            source_type=JobSource.SourceType.LEVER,
            base_url="https://jobs.lever.co/launchpoint",
            last_scanned_at=timezone.now(),
            scan_interval_hours=24,
        )

        with patch("core.services.job_discovery.scan_source") as mocked_scan:
            mocked_scan.side_effect = lambda source: type("Result", (), {"source": source, "summary": type("Summary", (), {"discovered_count": 0, "created_count": 0, "duplicate_count": 0, "failed_count": 0, "skipped_count": 0, "errors": []})()})()
            result = scan_all_sources(due_only=True)

        assert len(result.sources) == 1
        assert result.sources[0].source.id == due_source.id
        assert result.sources[0].source.id != not_due_source.id


class JobDiscoveryApiTests(APITestCase):
    def setUp(self):
        self.source = JobSource.objects.create(
            name="Orbit Labs Internships",
            company_name="Orbit Labs",
            source_type=JobSource.SourceType.GREENHOUSE,
            base_url="https://boards.greenhouse.io/orbitlabs",
            scan_interval_hours=24,
        )

    def test_source_crud_and_scan_flow(self):
        create_response = self.client.post(
            "/api/v1/sources",
            {
                "name": "Launch Point Internships",
                "company_name": "Launch Point",
                "source_type": "LEVER",
                "base_url": "https://jobs.lever.co/launchpoint/",
                "scan_interval_hours": 12,
                "is_active": True,
            },
            format="json",
        )

        assert create_response.status_code == 201
        assert create_response.data["base_url"] == "https://jobs.lever.co/launchpoint"

        patch_response = self.client.patch(
            f"/api/v1/sources/{create_response.data['id']}",
            {"is_active": False},
            format="json",
        )

        assert patch_response.status_code == 200
        assert patch_response.data["is_active"] is False

        list_response = self.client.get("/api/v1/sources")
        assert list_response.status_code == 200
        assert len(list_response.data) == 2

    def test_scan_source_returns_created_duplicate_failed_and_skipped_summary(self):
        with patch("core.services.job_discovery.fetch_json_document") as mocked_board_fetch:
            mocked_board_fetch.return_value = json.loads(load_sample("greenhouse_board.json"))

            with patch("core.services.job_ingestion.fetch_url_document") as mocked_job_fetch:
                mocked_job_fetch.return_value = FetchedDocument(
                    final_url="https://boards.greenhouse.io/orbitlabs/jobs/gh-12345",
                    html=load_sample("greenhouse_job.html"),
                )
                first_response = self.client.post(f"/api/v1/sources/{self.source.id}/scan", {}, format="json")

            with patch("core.services.job_ingestion.fetch_url_document") as mocked_job_fetch:
                mocked_job_fetch.return_value = FetchedDocument(
                    final_url="https://boards.greenhouse.io/orbitlabs/jobs/gh-12345",
                    html=load_sample("greenhouse_job.html"),
                )
                second_response = self.client.post(f"/api/v1/sources/{self.source.id}/scan", {}, format="json")

        assert first_response.status_code == 200
        assert first_response.data["summary"]["discovered_count"] == 1
        assert first_response.data["summary"]["created_count"] == 1
        assert first_response.data["summary"]["duplicate_count"] == 0
        assert second_response.status_code == 200
        assert second_response.data["summary"]["duplicate_count"] == 1
        assert Job.objects.count() == 1

    def test_scan_source_updates_last_seen_at_for_duplicates(self):
        existing_job = Job.objects.create(
            company_name="Orbit Labs",
            title="Backend Software Engineer Intern",
            location="San Francisco, CA",
            raw_text=load_sample("sample_job_backend.txt"),
            source_type=Job.SourceType.GREENHOUSE,
            source_url="https://boards.greenhouse.io/orbitlabs/jobs/gh-12345",
            content_hash="content-hash-1",
            last_seen_at=timezone.now() - timedelta(days=2),
            ingestion_status=Job.IngestionStatus.INGESTED,
            normalized_requirements=["python"],
            normalized_preferred=[],
        )
        previous_seen_at = existing_job.last_seen_at

        with patch("core.services.job_discovery.fetch_json_document") as mocked_board_fetch:
            mocked_board_fetch.return_value = json.loads(load_sample("greenhouse_board.json"))
            response = self.client.post(f"/api/v1/sources/{self.source.id}/scan", {}, format="json")

        existing_job.refresh_from_db()
        assert response.status_code == 200
        assert existing_job.last_seen_at is not None
        assert previous_seen_at is not None
        assert existing_job.last_seen_at > previous_seen_at

    def test_scan_source_handles_provider_failure(self):
        with patch("core.services.job_discovery.fetch_json_document") as mocked_board_fetch:
            mocked_board_fetch.side_effect = Exception("boom")
            response = self.client.post(f"/api/v1/sources/{self.source.id}/scan", {}, format="json")

        assert response.status_code == 200
        assert response.data["summary"]["failed_count"] == 1
        assert response.data["source"]["last_error"] == "Unexpected discovery error while scanning the job source."

    def test_scan_all_returns_aggregate_summary_for_active_sources_only(self):
        inactive_source = JobSource.objects.create(
            name="Pine AI",
            company_name="Pine AI",
            source_type=JobSource.SourceType.ASHBY,
            base_url="https://jobs.ashbyhq.com/pine-ai",
            is_active=False,
        )

        with patch("core.services.job_discovery.fetch_source_listings") as mocked_scan:
            mocked_scan.side_effect = [
                [],
            ]
            response = self.client.post("/api/v1/sources/scan-all", {}, format="json")

        assert response.status_code == 200
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["source"]["id"] != str(inactive_source.id)

    def test_management_command_scans_due_sources(self):
        self.source.last_scanned_at = timezone.now() - timedelta(hours=30)
        self.source.save(update_fields=["last_scanned_at", "updated_at"])

        with patch("core.services.job_discovery.fetch_json_document") as mocked_board_fetch:
            mocked_board_fetch.return_value = json.loads(load_sample("greenhouse_board.json"))
            with patch("core.services.job_ingestion.fetch_url_document") as mocked_job_fetch:
                mocked_job_fetch.return_value = FetchedDocument(
                    final_url="https://boards.greenhouse.io/orbitlabs/jobs/gh-12345",
                    html=load_sample("greenhouse_job.html"),
                )
                call_command("scan_job_sources")

        self.source.refresh_from_db()
        assert self.source.last_scanned_at is not None
