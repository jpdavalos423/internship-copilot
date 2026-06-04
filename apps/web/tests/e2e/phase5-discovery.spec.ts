import { expect, test, type Page } from "@playwright/test";

type DiscoveryScanSummary = {
  discovered_count: number;
  created_count: number;
  duplicate_count: number;
  failed_count: number;
  skipped_count: number;
  errors: string[];
};

type JobSource = {
  id: string;
  name: string;
  source_type: "GREENHOUSE" | "LEVER" | "ASHBY";
  base_url: string;
  company_name: string;
  is_active: boolean;
  last_scanned_at: string | null;
  last_success_at: string | null;
  last_error: string;
  scan_interval_hours: number;
  last_scan_summary: DiscoveryScanSummary;
  created_at: string;
  updated_at: string;
};

type MockJob = {
  id: string;
  company_name: string;
  title: string;
  location: string;
  position_type?: "INTERN" | "FULL_TIME" | "PART_TIME" | "UNKNOWN";
  raw_text: string;
  source_type: "MANUAL" | "GREENHOUSE" | "LEVER" | "ASHBY" | "OTHER";
  source_url: string | null;
  external_id: string | null;
  content_hash: string | null;
  last_seen_at: string | null;
  ingestion_status: "MANUAL" | "INGESTED" | "FAILED";
  workflow_status: "DISCOVERED" | "SAVED" | "APPLIED" | "OA" | "INTERVIEW" | "FINAL_ROUND" | "OFFER" | "REJECTED" | "WITHDRAWN";
  applied_date: string | null;
  notes: string;
  next_action: string;
  next_action_due_date: string | null;
  is_archived: boolean;
  is_hidden: boolean;
  is_saved: boolean;
  normalized_requirements: string[];
  normalized_preferred: string[];
  relevance: "HIGHLY_RELEVANT" | "RELEVANT" | "REVIEW" | "NOT_RELEVANT";
  relevance_reasons: string[];
  relevance_flags: string[];
  relevance_last_evaluated_at: string | null;
  relevance_score: number | null;
  created_at: string;
  updated_at: string;
  latest_match_score: number | null;
  latest_recommendation: string | null;
  latest_match_report_id: string | null;
  latest_analysis_created_at: string | null;
};

type MockPreferences = {
  id: string;
  target_terms: string[];
  role_types: string[];
  position_types: Array<"INTERN" | "FULL_TIME" | "PART_TIME">;
  preferred_locations: string[];
  remote_preference: "REMOTE" | "HYBRID" | "ONSITE" | "ANY";
  preferred_industries: string[];
  excluded_keywords: string[];
  minimum_match_score: number;
  include_sponsorship_required_roles: boolean;
  include_clearance_required_roles: boolean;
  created_at: string;
  updated_at: string;
};

function buildEmptySummary(): DiscoveryScanSummary {
  return {
    discovered_count: 0,
    created_count: 0,
    duplicate_count: 0,
    failed_count: 0,
    skipped_count: 0,
    errors: [],
  };
}

async function mockSourceRoutes(page: Page) {
  const sources: JobSource[] = [];
  const jobs: MockJob[] = [
    {
      id: "99999999-9999-9999-9999-999999999999",
      company_name: "Legacy Labs",
      title: "Older Backend Intern",
      location: "Remote",
      position_type: "INTERN",
      raw_text: "Summer 2026 internship\nPython",
      source_type: "GREENHOUSE",
      source_url: "https://boards.greenhouse.io/legacy/jobs/999",
      external_id: "gh-999",
      content_hash: "content-999",
      last_seen_at: "2026-05-20T20:30:00Z",
      ingestion_status: "INGESTED",
      workflow_status: "DISCOVERED",
      applied_date: null,
      notes: "",
      next_action: "",
      next_action_due_date: null,
      is_archived: false,
      is_hidden: false,
      is_saved: false,
      normalized_requirements: ["python"],
      normalized_preferred: [],
      relevance: "RELEVANT",
      relevance_reasons: ["Older discovery."],
      relevance_flags: [],
      relevance_last_evaluated_at: "2026-05-20T20:30:00Z",
      relevance_score: 70,
      created_at: "2026-05-20T20:30:00Z",
      updated_at: "2026-05-20T20:30:00Z",
      latest_match_score: null,
      latest_recommendation: null,
      latest_match_report_id: null,
      latest_analysis_created_at: null,
    },
  ];
  const preferences: MockPreferences = {
    id: "44444444-4444-4444-4444-444444444444",
    target_terms: ["Summer 2027"],
    role_types: ["Backend", "Platform", "Systems"],
    position_types: ["INTERN"],
    preferred_locations: ["Remote", "San Francisco, CA"],
    remote_preference: "ANY",
    preferred_industries: [],
    excluded_keywords: [],
    minimum_match_score: 60,
    include_sponsorship_required_roles: false,
    include_clearance_required_roles: false,
    created_at: "2026-06-04T20:30:00Z",
    updated_at: "2026-06-04T20:30:00Z",
  };
  let lastJobsRequestUrl: string | null = null;

  await page.route("**/api/v1/preferences/recruiting", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(preferences),
    });
  });

  await page.route("**/api/v1/sources", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(sources),
      });
      return;
    }

    if (route.request().method() === "POST") {
      const payload = route.request().postDataJSON() as Partial<JobSource>;
      if (!payload.base_url || !String(payload.base_url).startsWith("https://")) {
        await route.fulfill({
          status: 400,
          contentType: "application/json",
          body: JSON.stringify({
            error: {
              code: "INVALID_SOURCE_URL",
              message: "Only provider-hosted Greenhouse, Lever, and Ashby board URLs are supported.",
            },
          }),
        });
        return;
      }

      const created: JobSource = {
        id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        name: String(payload.name),
        company_name: String(payload.company_name),
        source_type: payload.source_type as JobSource["source_type"],
        base_url: String(payload.base_url).replace(/\/$/, ""),
        is_active: payload.is_active ?? true,
        scan_interval_hours: Number(payload.scan_interval_hours ?? 24),
        last_scanned_at: null,
        last_success_at: null,
        last_error: "",
        last_scan_summary: buildEmptySummary(),
        created_at: "2026-06-04T20:30:00Z",
        updated_at: "2026-06-04T20:30:00Z",
      };
      sources.push(created);
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify(created),
      });
      return;
    }

    await route.fallback();
  });

  await page.route("**/api/v1/sources/scan-all", async (route) => {
    const updatedSources = sources.filter((source) => source.is_active).map((source, index) => {
      const summary: DiscoveryScanSummary =
        index === 0
          ? {
              discovered_count: 2,
              created_count: 1,
              duplicate_count: 1,
              failed_count: 0,
              skipped_count: 1,
              errors: [],
            }
          : buildEmptySummary();

      source.last_scanned_at = "2026-06-05T20:30:00Z";
      source.last_success_at = "2026-06-05T20:30:00Z";
      source.last_error = "";
      source.last_scan_summary = summary;
      return { source, summary };
    });

    if (updatedSources[0]) {
      jobs.push({
        id: "11111111-1111-1111-1111-111111111111",
        company_name: "Orbit Labs",
        title: "Backend Software Engineer Intern",
        location: "San Francisco, CA",
        raw_text: "Summer 2027 internship\nPython\nAWS",
        source_type: "GREENHOUSE",
        source_url: "https://boards.greenhouse.io/orbitlabs/jobs/gh-12345",
        external_id: "gh-12345",
        content_hash: "content-111",
        last_seen_at: "2026-06-05T20:30:00Z",
        ingestion_status: "INGESTED",
        workflow_status: "DISCOVERED",
        applied_date: null,
        notes: "",
        next_action: "",
        next_action_due_date: null,
        is_archived: false,
        is_hidden: false,
        is_saved: false,
        normalized_requirements: ["python"],
        normalized_preferred: ["aws"],
        relevance: "RELEVANT",
        relevance_reasons: ["Role alignment: Backend."],
        relevance_flags: [],
        relevance_last_evaluated_at: "2026-06-05T20:30:00Z",
        relevance_score: 74,
        created_at: "2026-06-05T20:30:00Z",
        updated_at: "2026-06-05T20:30:00Z",
        latest_match_score: null,
        latest_recommendation: null,
        latest_match_report_id: null,
        latest_analysis_created_at: null,
      });
      jobs.push({
        id: "22222222-2222-2222-2222-222222222222",
        company_name: "Signal Defense",
        title: "Security Research Intern",
        location: "Remote",
        position_type: "INTERN",
        raw_text: "Summer 2027 internship\nClearance preferred",
        source_type: "ASHBY",
        source_url: "https://jobs.ashbyhq.com/signal/jobs/222",
        external_id: "ashby-222",
        content_hash: "content-222",
        last_seen_at: "2026-06-05T20:30:00Z",
        ingestion_status: "INGESTED",
        workflow_status: "DISCOVERED",
        applied_date: null,
        notes: "",
        next_action: "",
        next_action_due_date: null,
        is_archived: false,
        is_hidden: false,
        is_saved: false,
        normalized_requirements: ["security"],
        normalized_preferred: [],
        relevance: "NOT_RELEVANT",
        relevance_reasons: ["Out of scope."],
        relevance_flags: ["Requires a niche security focus."],
        relevance_last_evaluated_at: "2026-06-05T20:30:00Z",
        relevance_score: 20,
        created_at: "2026-06-05T20:30:00Z",
        updated_at: "2026-06-05T20:30:00Z",
        latest_match_score: null,
        latest_recommendation: null,
        latest_match_report_id: null,
        latest_analysis_created_at: null,
      });
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        summary: {
          discovered_count: 2,
          created_count: 1,
          duplicate_count: 1,
          failed_count: 0,
          skipped_count: 1,
          errors: [],
        },
        results: updatedSources,
      }),
    });
  });

  await page.route("**/api/v1/sources/*/scan", async (route) => {
    const sourceId = route.request().url().split("/sources/")[1].split("/scan")[0];
    const source = sources.find((item) => item.id === sourceId);
    if (!source) {
      await route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ error: { code: "JOB_SOURCE_NOT_FOUND", message: "Job source not found" } }) });
      return;
    }

    if (source.company_name === "Fail Corp") {
      source.last_scanned_at = "2026-06-05T21:30:00Z";
      source.last_error = "Unexpected discovery error while scanning the job source.";
      source.last_scan_summary = {
        discovered_count: 0,
        created_count: 0,
        duplicate_count: 0,
        failed_count: 1,
        skipped_count: 0,
        errors: ["Unexpected discovery error while scanning the job source."],
      };
    } else {
      source.last_scanned_at = "2026-06-05T21:30:00Z";
      source.last_success_at = "2026-06-05T21:30:00Z";
      source.last_error = "";
      source.last_scan_summary = {
        discovered_count: 1,
        created_count: 1,
        duplicate_count: 0,
        failed_count: 0,
        skipped_count: 0,
        errors: [],
      };
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        source,
        summary: source.last_scan_summary,
      }),
    });
  });

  await page.route("**/api/v1/sources/*", async (route) => {
    if (route.request().method() !== "PATCH") {
      await route.fallback();
      return;
    }

    const sourceId = route.request().url().split("/sources/")[1];
    const source = sources.find((item) => item.id === sourceId);
    if (!source) {
      await route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ error: { code: "JOB_SOURCE_NOT_FOUND", message: "Job source not found" } }) });
      return;
    }

    const payload = route.request().postDataJSON() as Partial<JobSource>;
    Object.assign(source, payload, { updated_at: "2026-06-05T20:35:00Z" });
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(source),
    });
  });

  await page.route("**/api/v1/jobs?**", async (route) => {
    lastJobsRequestUrl = route.request().url();
    const url = new URL(lastJobsRequestUrl);
    const view = url.searchParams.get("view");
    const recentlyAdded = url.searchParams.get("recently_added") === "true";
    const includeArchived = url.searchParams.get("include_archived") === "true";
    const hideNotRelevant = url.searchParams.get("hide_not_relevant") === "true";
    const status = url.searchParams.get("status");
    const relevance = url.searchParams.get("relevance");
    const sort = url.searchParams.get("sort");
    const recentThreshold = new Date("2026-05-29T00:00:00Z").getTime();

    let result = [...jobs];

    if (!includeArchived) {
      result = result.filter((job) => !job.is_archived);
    }
    if (view === "relevant" && !relevance) {
      result = result.filter((job) => ["HIGHLY_RELEVANT", "RELEVANT"].includes(job.relevance));
    }
    if (hideNotRelevant) {
      result = result.filter((job) => job.relevance !== "NOT_RELEVANT");
    }
    if (status) {
      const statuses = status.split(",");
      result = result.filter((job) => statuses.includes(job.workflow_status));
    }
    if (relevance) {
      const relevances = relevance.split(",");
      result = result.filter((job) => relevances.includes(job.relevance));
    }
    if (recentlyAdded) {
      result = result.filter((job) => new Date(job.created_at).getTime() >= recentThreshold);
    }
    if (sort === "newest_first" || sort === "created_at_desc") {
      result.sort((left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime());
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(result),
    });
  });

  return {
    sources,
    getLastJobsRequestUrl: () => lastJobsRequestUrl,
  };
}

test("adds a source, scans it, and shows the latest summary", async ({ page }) => {
  await mockSourceRoutes(page);

  await page.goto("/sources");
  await page.getByLabel("Source name").fill("Orbit Labs Internships");
  await page.getByLabel("Company name").fill("Orbit Labs");
  await page.getByLabel("Board URL").fill("https://boards.greenhouse.io/orbitlabs");
  await page.getByRole("button", { name: "Add Source" }).click();

  await expect(page.getByText("Source added successfully.")).toBeVisible();
  await expect(page.getByText("Orbit Labs Internships")).toBeVisible();

  await page.getByRole("button", { name: "Scan Now" }).click();
  await expect(page.getByText("Scan completed for Orbit Labs.")).toBeVisible();
  await expect(page.getByText("Last scan summary: 1 created, 0 duplicates, 0 failed, 0 skipped.")).toBeVisible();
});

test("shows a validation/backend error for unsupported source URLs", async ({ page }) => {
  await mockSourceRoutes(page);

  await page.goto("/sources");
  await page.getByLabel("Source name").fill("Bad Source");
  await page.getByLabel("Company name").fill("Bad Corp");
  await page.getByLabel("Board URL").fill("not-a-url");
  await page.getByRole("button", { name: "Add Source" }).click();

  await expect(page.getByText("Only provider-hosted Greenhouse, Lever, and Ashby board URLs are supported.")).toBeVisible();
});

test("handles a failed source scan and shows the saved error state", async ({ page }) => {
  const { sources } = await mockSourceRoutes(page);
  sources.push({
    id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    name: "Fail Corp Board",
    company_name: "Fail Corp",
    source_type: "LEVER",
    base_url: "https://jobs.lever.co/failcorp",
    is_active: true,
    scan_interval_hours: 24,
    last_scanned_at: null,
    last_success_at: null,
    last_error: "",
    last_scan_summary: buildEmptySummary(),
    created_at: "2026-06-04T20:30:00Z",
    updated_at: "2026-06-04T20:30:00Z",
  });

  await page.goto("/sources");
  const failCard = page.locator(".dashboard-job-card", { has: page.getByText("Fail Corp Board") });
  await failCard.getByRole("button", { name: "Scan Now" }).click();

  await expect(page.getByText("Unexpected discovery error while scanning the job source.")).toBeVisible();
});

test("scan all updates sources and discovered jobs appear in the Personalized Job Board", async ({ page }) => {
  const { getLastJobsRequestUrl } = await mockSourceRoutes(page);

  await page.goto("/sources");
  await page.getByLabel("Source name").fill("Orbit Labs Internships");
  await page.getByLabel("Company name").fill("Orbit Labs");
  await page.getByLabel("Board URL").fill("https://boards.greenhouse.io/orbitlabs");
  await page.getByRole("button", { name: "Add Source" }).click();
  await expect(page.getByText("Source added successfully.")).toBeVisible();

  await page.getByRole("button", { name: "Scan All" }).click();
  await expect(page.getByText("Scan all completed.")).toBeVisible();

  await page.getByRole("link", { name: "View discovered jobs" }).click();
  await expect(page).toHaveURL(/\/jobs\?view=all&recently_added=true$/);
  await expect(page.getByRole("heading", { name: "All Jobs" })).toBeVisible();
  await expect(page.getByText("Orbit Labs")).toBeVisible();
  await expect(page.getByText("Backend Software Engineer Intern")).toBeVisible();
  await expect(page.getByText("Signal Defense")).toBeVisible();
  await expect(page.getByText("Legacy Labs")).toHaveCount(0);
  await expect(page.getByText("Unknown")).toBeVisible();

  const lastJobsRequestUrl = getLastJobsRequestUrl();
  expect(lastJobsRequestUrl).not.toBeNull();
  const lastJobsRequest = new URL(lastJobsRequestUrl ?? "http://127.0.0.1");
  expect(lastJobsRequest.searchParams.get("view")).toBe("all");
  expect(lastJobsRequest.searchParams.get("recently_added")).toBe("true");
  expect(lastJobsRequest.searchParams.get("position_type")).toBeNull();
});

test("disabling a source updates the UI state before scan all", async ({ page }) => {
  await mockSourceRoutes(page);

  await page.goto("/sources");
  await page.getByLabel("Source name").fill("Orbit Labs Internships");
  await page.getByLabel("Company name").fill("Orbit Labs");
  await page.getByLabel("Board URL").fill("https://boards.greenhouse.io/orbitlabs");
  await page.getByRole("button", { name: "Add Source" }).click();

  await page.getByRole("button", { name: "Disable" }).click();
  await expect(page.getByText("Source disabled.")).toBeVisible();
  await expect(page.getByText("Disabled", { exact: true })).toBeVisible();
});
