from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from django.db.models import QuerySet
from django.utils import timezone

from core.models import JobSource, default_scan_summary
from core.services.job_ingestion import JobIngestionError, ingest_job_from_url
from core.services.relevance import get_or_create_preferences, refresh_job_relevance

FETCH_TIMEOUT_SECONDS = 10
USER_AGENT = "InternshipCopilot/phase5-discovery (+https://localhost)"
INCLUDE_KEYWORDS = [
    "intern",
    "internship",
    "co-op",
    "coop",
    "software",
    "engineer",
    "backend",
    "frontend",
    "full-stack",
    "full stack",
    "platform",
    "infrastructure",
    "systems",
    "data",
    "ml",
    "machine learning",
    "cloud",
]
EXCLUDE_KEYWORDS = [
    "senior",
    "staff",
    "principal",
    "manager",
    "director",
    "sales",
    "recruiter",
]


class JobDiscoveryError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class DiscoveredListing:
    url: str
    title: str
    location: str
    source_type: str


@dataclass
class DiscoveryScanSummary:
    discovered_count: int = 0
    created_count: int = 0
    duplicate_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "discovered_count": self.discovered_count,
            "created_count": self.created_count,
            "duplicate_count": self.duplicate_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "errors": self.errors,
        }


@dataclass
class SourceScanResult:
    source: JobSource
    summary: DiscoveryScanSummary


@dataclass
class ScanAllSourcesResult:
    sources: list[SourceScanResult]
    summary: DiscoveryScanSummary


def normalize_source_base_url(url: str, expected_source_type: str | None = None) -> tuple[str, str]:
    parsed = urlsplit(url.strip())
    hostname = (parsed.hostname or "").lower()
    path_parts = [part for part in parsed.path.split("/") if part]

    if parsed.scheme.lower() not in {"http", "https"} or not hostname or not path_parts:
        raise JobDiscoveryError("Enter a valid supported provider-hosted board URL.")

    if hostname == "boards.greenhouse.io" and len(path_parts) >= 1:
        normalized = f"https://boards.greenhouse.io/{path_parts[0]}"
        source_type = JobSource.SourceType.GREENHOUSE
    elif hostname in {"jobs.lever.co", "jobs.eu.lever.co"} and len(path_parts) == 1:
        normalized = f"https://{hostname}/{path_parts[0]}"
        source_type = JobSource.SourceType.LEVER
    elif hostname == "jobs.ashbyhq.com" and len(path_parts) == 1:
        normalized = f"https://jobs.ashbyhq.com/{path_parts[0]}"
        source_type = JobSource.SourceType.ASHBY
    else:
        raise JobDiscoveryError(
            "Only provider-hosted Greenhouse, Lever, and Ashby board URLs are supported."
        )

    if expected_source_type is not None and expected_source_type != source_type:
        raise JobDiscoveryError("Source type does not match the selected provider-hosted board URL.")

    return source_type, normalized


def fetch_json_document(url: str) -> Any:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            payload = response.read().decode(charset, errors="replace")
            return json.loads(payload)
    except HTTPError as exc:
        raise JobDiscoveryError(f"Board request failed with HTTP {exc.code}.") from exc
    except URLError as exc:
        raise JobDiscoveryError("Failed to reach the provider job board API.") from exc
    except TimeoutError as exc:
        raise JobDiscoveryError("Fetching the provider job board timed out.") from exc
    except json.JSONDecodeError as exc:
        raise JobDiscoveryError("Provider job board API returned invalid JSON.") from exc


def _coerce_text(value: Any) -> str:
    return str(value or "").strip()


def _parse_greenhouse_listings(base_url: str) -> list[DiscoveredListing]:
    board_token = base_url.rstrip("/").split("/")[-1]
    payload = fetch_json_document(
        f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
    )
    jobs = payload.get("jobs")
    if not isinstance(jobs, list):
        raise JobDiscoveryError("Greenhouse board response was missing its jobs list.")

    listings: list[DiscoveredListing] = []
    for job in jobs:
        if not isinstance(job, dict):
            continue
        if job.get("internal_job_id") is None:
            continue
        listings.append(
            DiscoveredListing(
                url=_coerce_text(job.get("absolute_url")),
                title=_coerce_text(job.get("title")),
                location=_coerce_text((job.get("location") or {}).get("name")),
                source_type=JobSource.SourceType.GREENHOUSE,
            )
        )
    return [listing for listing in listings if listing.url and listing.title]


def _parse_lever_page(items: list[dict[str, Any]]) -> list[DiscoveredListing]:
    listings: list[DiscoveredListing] = []
    for item in items:
        categories = item.get("categories") or {}
        listings.append(
            DiscoveredListing(
                url=_coerce_text(item.get("hostedUrl")),
                title=_coerce_text(item.get("text")),
                location=_coerce_text(categories.get("location")),
                source_type=JobSource.SourceType.LEVER,
            )
        )
    return [listing for listing in listings if listing.url and listing.title]


def _parse_lever_listings(base_url: str) -> list[DiscoveredListing]:
    parsed = urlsplit(base_url)
    site = parsed.path.strip("/").split("/")[0]
    api_host = "api.eu.lever.co" if parsed.hostname == "jobs.eu.lever.co" else "api.lever.co"

    all_listings: list[DiscoveredListing] = []
    skip = 0
    limit = 50

    while True:
        payload = fetch_json_document(
            f"https://{api_host}/v0/postings/{site}?mode=json&skip={skip}&limit={limit}"
        )
        if not isinstance(payload, list):
            raise JobDiscoveryError("Lever board response was not a JSON list.")
        page_items = [item for item in payload if isinstance(item, dict)]
        all_listings.extend(_parse_lever_page(page_items))
        if len(page_items) < limit:
            break
        skip += limit

    return all_listings


def _parse_ashby_listings(base_url: str) -> list[DiscoveredListing]:
    board_name = base_url.rstrip("/").split("/")[-1]
    payload = fetch_json_document(
        f"https://api.ashbyhq.com/posting-api/job-board/{board_name}"
    )
    jobs = payload.get("jobs")
    if not isinstance(jobs, list):
        raise JobDiscoveryError("Ashby board response was missing its jobs list.")

    listings: list[DiscoveredListing] = []
    for job in jobs:
        if not isinstance(job, dict) or job.get("isListed") is False:
            continue
        listings.append(
            DiscoveredListing(
                url=_coerce_text(job.get("jobUrl")),
                title=_coerce_text(job.get("title")),
                location=_coerce_text(job.get("location")),
                source_type=JobSource.SourceType.ASHBY,
            )
        )
    return [listing for listing in listings if listing.url and listing.title]


def fetch_source_listings(source: JobSource) -> list[DiscoveredListing]:
    if source.source_type == JobSource.SourceType.GREENHOUSE:
        return _parse_greenhouse_listings(source.base_url)
    if source.source_type == JobSource.SourceType.LEVER:
        return _parse_lever_listings(source.base_url)
    if source.source_type == JobSource.SourceType.ASHBY:
        return _parse_ashby_listings(source.base_url)
    raise JobDiscoveryError("Unsupported source type.")


def _normalize_search_text(*parts: str) -> str:
    text = " ".join(part for part in parts if part)
    return re.sub(r"\s+", " ", text).strip().lower()


def is_target_listing(listing: DiscoveredListing) -> bool:
    search_text = _normalize_search_text(listing.title, listing.location)
    has_excluded_term = any(keyword in search_text for keyword in EXCLUDE_KEYWORDS)
    if has_excluded_term:
        return False

    has_include_term = any(keyword in search_text for keyword in INCLUDE_KEYWORDS)
    if has_include_term:
        return True

    return "engineer" in search_text or "developer" in search_text


def _aggregate_summaries(summaries: list[DiscoveryScanSummary]) -> DiscoveryScanSummary:
    aggregate = DiscoveryScanSummary()
    for summary in summaries:
        aggregate.discovered_count += summary.discovered_count
        aggregate.created_count += summary.created_count
        aggregate.duplicate_count += summary.duplicate_count
        aggregate.failed_count += summary.failed_count
        aggregate.skipped_count += summary.skipped_count
        aggregate.errors.extend(summary.errors)
    return aggregate


def scan_source(source: JobSource) -> SourceScanResult:
    started_at = timezone.now()
    summary = DiscoveryScanSummary()
    preferences = get_or_create_preferences()

    try:
        listings = fetch_source_listings(source)
        summary.discovered_count = len(listings)

        for listing in listings:
            if not is_target_listing(listing):
                summary.skipped_count += 1
                continue

            try:
                result = ingest_job_from_url(listing.url)
            except JobIngestionError as exc:
                summary.failed_count += 1
                summary.errors.append(f"{listing.title}: {exc.message}")
                continue

            if result.created:
                summary.created_count += 1
            else:
                summary.duplicate_count += 1

            refresh_job_relevance(result.job, preferences=preferences)

        source.last_scanned_at = started_at
        source.last_success_at = started_at
        source.last_error = ""
        source.last_scan_summary = summary.to_dict()
        source.save(
            update_fields=[
                "last_scanned_at",
                "last_success_at",
                "last_error",
                "last_scan_summary",
                "updated_at",
            ]
        )
    except JobDiscoveryError as exc:
        summary.failed_count += 1
        summary.errors.append(exc.message)
        source.last_scanned_at = started_at
        source.last_error = exc.message
        source.last_scan_summary = summary.to_dict()
        source.save(
            update_fields=[
                "last_scanned_at",
                "last_error",
                "last_scan_summary",
                "updated_at",
            ]
        )
    except Exception:
        message = "Unexpected discovery error while scanning the job source."
        summary.failed_count += 1
        summary.errors.append(message)
        source.last_scanned_at = started_at
        source.last_error = message
        source.last_scan_summary = summary.to_dict()
        source.save(
            update_fields=[
                "last_scanned_at",
                "last_error",
                "last_scan_summary",
                "updated_at",
            ]
        )

    return SourceScanResult(source=source, summary=summary)


def get_active_sources(*, due_only: bool = False) -> QuerySet[JobSource]:
    queryset = JobSource.objects.filter(is_active=True)
    if not due_only:
        return queryset

    now = timezone.now()
    due_ids: list[object] = []
    for source in queryset:
        if source.last_scanned_at is None:
            due_ids.append(source.id)
            continue
        next_due_at = source.last_scanned_at + timedelta(hours=source.scan_interval_hours)
        if next_due_at <= now:
            due_ids.append(source.id)
    return queryset.filter(id__in=due_ids)


def scan_all_sources(*, due_only: bool = False) -> ScanAllSourcesResult:
    results = [scan_source(source) for source in get_active_sources(due_only=due_only)]
    return ScanAllSourcesResult(
        sources=results,
        summary=_aggregate_summaries([result.summary for result in results]),
    )


def empty_scan_summary() -> dict[str, object]:
    return default_scan_summary()
