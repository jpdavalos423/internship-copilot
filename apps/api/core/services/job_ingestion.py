import hashlib
import json
import re
from dataclasses import dataclass
from html import unescape
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

from django.utils import timezone
from django.utils.html import strip_tags

from core.models import Job
from core.services.job_parser import parse_job_text

FETCH_TIMEOUT_SECONDS = 10
USER_AGENT = "InternshipCopilot/phase2 (+https://localhost)"
BLOCK_TAG_PATTERN = re.compile(r"</(p|div|section|article|main|li|ul|ol|h[1-6]|br|tr|td)>", re.IGNORECASE)
SCRIPT_STYLE_PATTERN = re.compile(
    r"<(script|style|noscript|svg|template)\b[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)
JSON_LD_PATTERN = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
TITLE_PATTERN = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
H1_PATTERN = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
META_PATTERN = re.compile(
    r"<meta\b(?P<attrs>[^>]*?(?:name|property)=['\"](?P<name>[^'\"]+)['\"][^>]*)>",
    re.IGNORECASE,
)
CONTENT_PATTERN = re.compile(r"content=['\"](?P<content>[^'\"]*)['\"]", re.IGNORECASE)
TEXT_BLOCK_PATTERN = re.compile(
    r"<(?P<tag>main|article|section|div)[^>]*(?:id|class)=['\"][^'\"]*"
    r"(?P<keyword>job|posting|description|content|main|role|details)[^'\"]*['\"][^>]*>"
    r"(?P<body>.*?)</(?P=tag)>",
    re.IGNORECASE | re.DOTALL,
)
LOCATION_PATTERN = re.compile(
    r"<(?P<tag>div|span|p|li)[^>]*(?:id|class)=['\"][^'\"]*location[^'\"]*['\"][^>]*>(?P<body>.*?)</(?P=tag)>",
    re.IGNORECASE | re.DOTALL,
)
COMPANY_PATTERN = re.compile(
    r"<(?P<tag>div|span|p)[^>]*(?:id|class)=['\"][^'\"]*(company|organization)[^'\"]*['\"][^>]*>(?P<body>.*?)</(?P=tag)>",
    re.IGNORECASE | re.DOTALL,
)
HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
WHITESPACE_PATTERN = re.compile(r"[ \t]+")
MULTI_NEWLINE_PATTERN = re.compile(r"\n{3,}")


class JobIngestionError(Exception):
    def __init__(self, message: str, *, code: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


@dataclass(frozen=True)
class FetchedDocument:
    final_url: str
    html: str


@dataclass(frozen=True)
class ExtractedJobPosting:
    company_name: str
    title: str
    location: str
    raw_text: str
    source_type: str
    source_url: str
    external_id: str | None
    content_hash: str


def normalize_job_url(url: str) -> str:
    raw_url = url.strip()
    parsed = urlsplit(raw_url)

    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise JobIngestionError(
            "Enter a valid http or https job posting URL.",
            code="INVALID_URL",
            status_code=400,
        )

    hostname = parsed.hostname.lower()
    port = parsed.port
    include_port = port and not (
        (parsed.scheme.lower() == "http" and port == 80)
        or (parsed.scheme.lower() == "https" and port == 443)
    )
    netloc = f"{hostname}:{port}" if include_port else hostname
    path = parsed.path or "/"

    return urlunsplit((parsed.scheme.lower(), netloc, path, parsed.query, ""))


def detect_source_type(url: str) -> str:
    host = urlsplit(url).hostname or ""

    if "greenhouse.io" in host:
        return Job.SourceType.GREENHOUSE
    if "lever.co" in host:
        return Job.SourceType.LEVER
    if "ashbyhq.com" in host:
        return Job.SourceType.ASHBY
    return Job.SourceType.OTHER


def fetch_url_document(url: str) -> FetchedDocument:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        },
    )

    try:
        with urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
            content_type = response.headers.get_content_type()
            if content_type not in {"text/html", "application/xhtml+xml"}:
                raise JobIngestionError(
                    "The URL did not return an HTML job posting page.",
                    code="JOB_FETCH_FAILED",
                    status_code=502,
                )

            charset = response.headers.get_content_charset() or "utf-8"
            html = response.read().decode(charset, errors="replace")
            return FetchedDocument(final_url=response.geturl(), html=html)
    except JobIngestionError:
        raise
    except HTTPError as exc:
        raise JobIngestionError(
            f"Failed to fetch the job posting. The source returned HTTP {exc.code}.",
            code="JOB_FETCH_FAILED",
            status_code=502,
        ) from exc
    except URLError as exc:
        raise JobIngestionError(
            "Failed to fetch the job posting URL.",
            code="JOB_FETCH_FAILED",
            status_code=502,
        ) from exc
    except TimeoutError as exc:
        raise JobIngestionError(
            "Fetching the job posting timed out.",
            code="JOB_FETCH_FAILED",
            status_code=502,
        ) from exc


def _html_to_text(html: str) -> str:
    without_comments = HTML_COMMENT_PATTERN.sub("", html)
    without_noise = SCRIPT_STYLE_PATTERN.sub(" ", without_comments)
    with_breaks = BLOCK_TAG_PATTERN.sub("\n", without_noise)
    stripped = strip_tags(with_breaks)
    decoded = unescape(stripped).replace("\r", "")
    collapsed = WHITESPACE_PATTERN.sub(" ", decoded)
    normalized = MULTI_NEWLINE_PATTERN.sub("\n\n", collapsed)
    lines = [line.strip() for line in normalized.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _extract_meta_tags(html: str) -> dict[str, str]:
    tags: dict[str, str] = {}
    for match in META_PATTERN.finditer(html):
        name = match.group("name").strip().lower()
        attrs = match.group("attrs")
        content_match = CONTENT_PATTERN.search(attrs)
        if content_match:
            tags[name] = unescape(content_match.group("content")).strip()
    return tags


def _flatten_json_ld(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        items: list[dict[str, Any]] = []
        for item in data:
            items.extend(_flatten_json_ld(item))
        return items
    if isinstance(data, dict):
        items = [data]
        graph = data.get("@graph")
        if isinstance(graph, list):
            items.extend(_flatten_json_ld(graph))
        return items
    return []


def _extract_job_posting_schema(html: str) -> dict[str, Any]:
    for match in JSON_LD_PATTERN.finditer(html):
        try:
            parsed = json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            continue
        for item in _flatten_json_ld(parsed):
            item_type = item.get("@type")
            if item_type == "JobPosting" or (isinstance(item_type, list) and "JobPosting" in item_type):
                return item
    return {}


def _text_from_html_fragment(fragment: str) -> str:
    return _html_to_text(fragment)


def _first_match_text(pattern: re.Pattern[str], html: str) -> str | None:
    match = pattern.search(html)
    if not match:
        return None
    return _text_from_html_fragment(match.group(match.lastgroup or 1))


def _extract_candidate_text_blocks(html: str) -> list[str]:
    blocks = [_html_to_text(match.group("body")) for match in TEXT_BLOCK_PATTERN.finditer(html)]
    return [block for block in blocks if block]


def _extract_title(html: str, source_type: str, metadata: dict[str, str], schema: dict[str, Any]) -> str:
    schema_title = str(schema.get("title") or "").strip()
    if schema_title:
        return schema_title

    for key in ("og:title", "twitter:title"):
        if metadata.get(key):
            title_text = metadata[key]
            if source_type in {Job.SourceType.GREENHOUSE, Job.SourceType.LEVER, Job.SourceType.ASHBY}:
                return re.split(r"\s+[|\-]\s+", title_text, maxsplit=1)[0].strip()
            return title_text

    h1_text = _first_match_text(H1_PATTERN, html)
    if h1_text:
        return h1_text

    title_match = TITLE_PATTERN.search(html)
    if title_match:
        title_text = _text_from_html_fragment(title_match.group(1))
        if source_type in {Job.SourceType.GREENHOUSE, Job.SourceType.LEVER, Job.SourceType.ASHBY}:
            return re.split(r"\s+[|\-]\s+", title_text, maxsplit=1)[0].strip()
        return title_text

    return ""


def _format_schema_location(value: Any) -> str:
    if isinstance(value, list):
        for item in value:
            location = _format_schema_location(item)
            if location:
                return location
        return ""

    if not isinstance(value, dict):
        return ""

    address = value.get("address", value)
    if isinstance(address, dict):
        parts = [
            str(address.get("addressLocality") or "").strip(),
            str(address.get("addressRegion") or "").strip(),
            str(address.get("addressCountry") or "").strip(),
        ]
        return ", ".join(part for part in parts if part)

    return ""


def _extract_location(html: str, metadata: dict[str, str], schema: dict[str, Any]) -> str:
    schema_location = _format_schema_location(schema.get("jobLocation"))
    if schema_location:
        return schema_location

    location_text = _first_match_text(LOCATION_PATTERN, html)
    if location_text:
        return location_text

    for key in ("job:location", "og:locality"):
        if metadata.get(key):
            return metadata[key]

    return ""


def _slug_to_name(slug: str) -> str:
    cleaned = re.sub(r"[-_]+", " ", slug).strip()
    return cleaned.title() if cleaned else ""


def _extract_company_name(
    html: str,
    source_url: str,
    source_type: str,
    metadata: dict[str, str],
    schema: dict[str, Any],
) -> str:
    hiring_org = schema.get("hiringOrganization")
    if isinstance(hiring_org, dict):
        schema_company = str(hiring_org.get("name") or "").strip()
        if schema_company:
            return schema_company

    company_text = _first_match_text(COMPANY_PATTERN, html)
    if company_text:
        return company_text

    for key in ("og:site_name", "application-name"):
        if metadata.get(key):
            return metadata[key]

    title_text = metadata.get("og:title") or ""
    for separator in (" | ", " - "):
        if separator in title_text:
            parts = [part.strip() for part in title_text.split(separator) if part.strip()]
            if len(parts) >= 2:
                return parts[-1]

    path_parts = [part for part in urlsplit(source_url).path.split("/") if part]
    if source_type in {Job.SourceType.GREENHOUSE, Job.SourceType.LEVER, Job.SourceType.ASHBY} and path_parts:
        return _slug_to_name(path_parts[0])

    return ""


def _extract_external_id(source_url: str, schema: dict[str, Any]) -> str | None:
    identifier = schema.get("identifier")
    if isinstance(identifier, dict):
        value = str(identifier.get("value") or "").strip()
        if value:
            return value
    elif isinstance(identifier, str) and identifier.strip():
        return identifier.strip()

    path_parts = [part for part in urlsplit(source_url).path.split("/") if part]
    if path_parts:
        return path_parts[-1]
    return None


def _extract_raw_text(html: str, schema: dict[str, Any]) -> str:
    description = schema.get("description")
    if isinstance(description, str):
        schema_text = _html_to_text(description)
        if schema_text:
            return schema_text

    candidate_blocks = _extract_candidate_text_blocks(html)
    if candidate_blocks:
        return max(candidate_blocks, key=len)

    body_match = re.search(r"<body[^>]*>(.*?)</body>", html, re.IGNORECASE | re.DOTALL)
    if body_match:
        return _html_to_text(body_match.group(1))

    return _html_to_text(html)


def compute_content_hash(*, company_name: str, title: str, location: str, raw_text: str) -> str:
    canonical_parts = [
        title.strip(),
        company_name.strip(),
        location.strip(),
        raw_text.strip(),
    ]
    canonical = "\n".join(canonical_parts)
    canonical = WHITESPACE_PATTERN.sub(" ", canonical).strip()
    canonical = MULTI_NEWLINE_PATTERN.sub("\n\n", canonical)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def extract_job_posting(*, source_url: str, html: str, source_type: str) -> ExtractedJobPosting:
    metadata = _extract_meta_tags(html)
    schema = _extract_job_posting_schema(html)

    title = _extract_title(html, source_type, metadata, schema).strip()
    company_name = _extract_company_name(html, source_url, source_type, metadata, schema).strip()
    location = _extract_location(html, metadata, schema).strip()
    raw_text = _extract_raw_text(html, schema).strip()

    if not raw_text:
        raise JobIngestionError(
            "The job page was fetched successfully, but no job description text could be extracted.",
            code="JOB_EXTRACTION_EMPTY",
            status_code=422,
        )

    if not title or not company_name:
        raise JobIngestionError(
            "The job page did not contain enough structured information to create a job record.",
            code="JOB_EXTRACTION_FAILED",
            status_code=422,
        )

    return ExtractedJobPosting(
        company_name=company_name,
        title=title,
        location=location,
        raw_text=raw_text,
        source_type=source_type,
        source_url=source_url,
        external_id=_extract_external_id(source_url, schema),
        content_hash=compute_content_hash(
            company_name=company_name,
            title=title,
            location=location,
            raw_text=raw_text,
        ),
    )


@dataclass(frozen=True)
class IngestJobResult:
    job: Job
    created: bool


def _touch_existing_job(job: Job) -> Job:
    job.last_seen_at = timezone.now()
    job.save(update_fields=["last_seen_at", "updated_at"])
    return job


def ingest_job_from_url(url: str) -> IngestJobResult:
    normalized_input_url = normalize_job_url(url)

    existing_by_input_url = Job.objects.filter(source_url=normalized_input_url).first()
    if existing_by_input_url is not None:
        return IngestJobResult(job=_touch_existing_job(existing_by_input_url), created=False)

    source_type = detect_source_type(normalized_input_url)
    fetched = fetch_url_document(normalized_input_url)
    normalized_final_url = normalize_job_url(fetched.final_url)

    existing_by_final_url = Job.objects.filter(source_url=normalized_final_url).first()
    if existing_by_final_url is not None:
        return IngestJobResult(job=_touch_existing_job(existing_by_final_url), created=False)

    extracted = extract_job_posting(
        source_url=normalized_final_url,
        html=fetched.html,
        source_type=source_type,
    )

    duplicate_by_hash = Job.objects.filter(content_hash=extracted.content_hash).first()
    if duplicate_by_hash is not None:
        return IngestJobResult(job=_touch_existing_job(duplicate_by_hash), created=False)

    parsed = parse_job_text(extracted.raw_text)
    job = Job.objects.create(
        company_name=extracted.company_name,
        title=extracted.title,
        location=extracted.location,
        raw_text=extracted.raw_text,
        source_type=extracted.source_type,
        source_url=extracted.source_url,
        external_id=extracted.external_id,
        content_hash=extracted.content_hash,
        last_seen_at=timezone.now(),
        ingestion_status=Job.IngestionStatus.INGESTED,
        normalized_requirements=parsed["requirements"],
        normalized_preferred=parsed["preferred"],
    )
    return IngestJobResult(job=job, created=True)
