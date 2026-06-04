import { expect, test, type Page } from "@playwright/test";

type MockJob = {
  id: string;
  company_name: string;
  title: string;
  location: string;
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
  relevance_score: number;
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

const baseJob = {
  raw_text: "Summer 2027 internship\nRequirements\nPython\nREST APIs",
  source_url: null,
  external_id: null,
  content_hash: null,
  last_seen_at: null,
  is_hidden: false,
  normalized_requirements: ["python", "rest apis"],
  normalized_preferred: ["aws"],
  relevance_last_evaluated_at: "2026-06-04T20:30:00Z",
  created_at: "2026-06-04T20:30:00Z",
  updated_at: "2026-06-04T20:30:00Z",
  latest_recommendation: null,
  latest_match_report_id: null,
  latest_analysis_created_at: null,
} satisfies Partial<MockJob>;

async function mockRecruitingRoutes(page: Page) {
  const jobs: MockJob[] = [
    {
      ...baseJob,
      id: "11111111-1111-1111-1111-111111111111",
      company_name: "Astranis",
      title: "Backend Intern",
      location: "San Francisco, CA",
      source_type: "MANUAL",
      ingestion_status: "MANUAL",
      workflow_status: "SAVED",
      applied_date: null,
      notes: "",
      next_action: "Tailor resume",
      next_action_due_date: "2026-06-08",
      is_archived: false,
      is_saved: true,
      relevance: "HIGHLY_RELEVANT",
      relevance_reasons: ["Match score 92 clears your 60 threshold."],
      relevance_flags: [],
      relevance_score: 92,
      latest_match_score: 92,
      latest_recommendation: "HIGH_PRIORITY_APPLY",
    },
    {
      ...baseJob,
      id: "22222222-2222-2222-2222-222222222222",
      company_name: "Orbit Labs",
      title: "Platform Intern",
      location: "Remote",
      source_type: "GREENHOUSE",
      source_url: "https://boards.greenhouse.io/orbit/jobs/222",
      external_id: "gh-222",
      content_hash: "content-222",
      last_seen_at: "2026-06-04T20:30:00Z",
      ingestion_status: "INGESTED",
      workflow_status: "DISCOVERED",
      applied_date: null,
      notes: "",
      next_action: "",
      next_action_due_date: null,
      is_archived: false,
      is_saved: false,
      relevance: "RELEVANT",
      relevance_reasons: ["Role alignment: Platform."],
      relevance_flags: [],
      relevance_score: 74,
      latest_match_score: 70,
      latest_recommendation: "REVIEW",
    },
    {
      ...baseJob,
      id: "33333333-3333-3333-3333-333333333333",
      company_name: "Pine AI",
      title: "Security Intern",
      location: "New York, NY",
      source_type: "ASHBY",
      source_url: "https://jobs.ashbyhq.com/pine/jobs/333",
      external_id: "ashby-333",
      content_hash: "content-333",
      last_seen_at: "2026-06-04T20:30:00Z",
      ingestion_status: "INGESTED",
      workflow_status: "REJECTED",
      applied_date: "2026-06-01",
      notes: "Closed out.",
      next_action: "",
      next_action_due_date: null,
      is_archived: false,
      is_saved: true,
      relevance: "NOT_RELEVANT",
      relevance_reasons: ["Match score 55 is below your 60 threshold."],
      relevance_flags: ["Role appears to require clearance."],
      relevance_score: 18,
      latest_match_score: 55,
      latest_recommendation: "LOW_PRIORITY",
    },
  ];

  const preferences: MockPreferences = {
    id: "44444444-4444-4444-4444-444444444444",
    target_terms: ["Fall 2026", "Winter 2027", "Spring 2027", "Summer 2027"],
    role_types: ["Backend", "Platform", "Systems", "Cloud"],
    preferred_locations: ["San Francisco, CA"],
    remote_preference: "ANY",
    preferred_industries: ["space"],
    excluded_keywords: [],
    minimum_match_score: 60,
    include_sponsorship_required_roles: false,
    include_clearance_required_roles: false,
    created_at: "2026-06-04T20:30:00Z",
    updated_at: "2026-06-04T20:30:00Z",
  };

  function sortJobs(result: MockJob[], sort: string) {
    return [...result].sort((left, right) => {
      if (sort === "match_score_asc") {
        return (left.latest_match_score ?? -1) - (right.latest_match_score ?? -1);
      }
      if (sort === "newest_first" || sort === "created_at_desc") {
        return new Date(right.created_at).getTime() - new Date(left.created_at).getTime();
      }
      return (right.latest_match_score ?? -1) - (left.latest_match_score ?? -1);
    });
  }

  await page.route("**/api/v1/preferences/recruiting", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(preferences),
      });
      return;
    }

    if (route.request().method() === "POST") {
      const payload = route.request().postDataJSON() as Partial<MockPreferences>;
      Object.assign(preferences, payload, { updated_at: "2026-06-05T20:30:00Z" });
      jobs[2].relevance = "REVIEW";
      jobs[2].relevance_reasons = ["Role alignment: Systems."];
      jobs[2].relevance_flags = [];
      jobs[2].relevance_score = 48;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(preferences),
      });
      return;
    }

    await route.fallback();
  });

  await page.route("**/api/v1/jobs?**", async (route) => {
    if (route.request().method() !== "GET") {
      await route.fallback();
      return;
    }

    const url = new URL(route.request().url());
    const relevanceFilter = url.searchParams.get("relevance");
    const statusFilter = url.searchParams.get("status");
    const includeArchived = url.searchParams.get("include_archived") === "true";
    const hideNotRelevant = url.searchParams.get("hide_not_relevant") === "true";
    const view = url.searchParams.get("view") ?? "relevant";
    const recentlyAdded = url.searchParams.get("recently_added") === "true";
    const sort = url.searchParams.get("sort") ?? "match_score_desc";

    let result = jobs.filter((job) => includeArchived || !job.is_archived);

    if (view === "relevant" && !relevanceFilter) {
      result = result.filter((job) => ["HIGHLY_RELEVANT", "RELEVANT"].includes(job.relevance));
    }

    if (hideNotRelevant) {
      result = result.filter((job) => job.relevance !== "NOT_RELEVANT");
    }

    if (relevanceFilter) {
      const values = relevanceFilter.split(",");
      result = result.filter((job) => values.includes(job.relevance));
    }

    if (statusFilter) {
      const statuses = statusFilter.split(",");
      result = result.filter((job) => statuses.includes(job.workflow_status));
    }

    if (recentlyAdded) {
      result = result.filter((job) => new Date(job.created_at).getTime() >= new Date("2026-05-29T00:00:00Z").getTime());
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(sortJobs(result, sort)),
    });
  });

  await page.route("**/api/v1/jobs", async (route) => {
    if (route.request().method() === "GET") {
      const result = jobs.filter((job) => ["HIGHLY_RELEVANT", "RELEVANT"].includes(job.relevance));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(sortJobs(result, "match_score_desc")),
      });
      return;
    }

    await route.fallback();
  });

  await page.route("**/api/v1/jobs/*", async (route) => {
    const url = new URL(route.request().url());
    const pathParts = url.pathname.split("/");
    const jobId = pathParts[4];
    const job = jobs.find((item) => item.id === jobId);

    if (!job) {
      await route.fulfill({
        status: 404,
        contentType: "application/json",
        body: JSON.stringify({
          error: {
            code: "JOB_NOT_FOUND",
            message: "Job not found",
          },
        }),
      });
      return;
    }

    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(job),
      });
      return;
    }

    if (route.request().method() === "PATCH") {
      const payload = route.request().postDataJSON() as Partial<MockJob>;
      Object.assign(job, payload);
      if (payload.workflow_status === "APPLIED" && !job.applied_date) {
        job.applied_date = "2026-06-04";
      }
      job.is_saved = job.workflow_status !== "DISCOVERED";
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(job),
      });
      return;
    }

    await route.fallback();
  });

  await page.route("**/api/v1/jobs/*/analysis", async (route) => {
    await route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({
        error: {
          code: "MATCH_REPORT_NOT_FOUND",
          message: "Match report not found",
        },
      }),
    });
  });
}

test("defaults to relevant jobs and supports switching to the full board", async ({ page }) => {
  await mockRecruitingRoutes(page);

  await page.goto("/jobs");

  await expect(page.getByRole("heading", { name: "Personalized Job Board" })).toBeVisible();
  await expect(page.locator(".stat").filter({ hasText: "Highly relevant" })).toContainText("1");
  await expect(page.locator(".stat").filter({ hasText: "Relevant" }).first()).toContainText("1");
  await expect(page.getByText("Astranis")).toBeVisible();
  await expect(page.getByText("Orbit Labs")).toBeVisible();
  await expect(page.getByText("Pine AI")).toHaveCount(0);
  await expect(page.getByText("Match score 92 clears your 60 threshold.")).toBeVisible();

  await page.getByRole("button", { name: "All Jobs" }).click();
  await page.getByLabel("Hide not-relevant jobs").uncheck();
  await expect(page.getByText("Pine AI")).toBeVisible();
  await expect(page.getByText("Role appears to require clearance.")).toBeVisible();
});

test("supports relevance filtering, newest-first sorting, and workflow quick actions", async ({ page }) => {
  await mockRecruitingRoutes(page);

  await page.goto("/jobs");
  await page.getByLabel("Relevance").selectOption("RELEVANT");
  await expect(page.getByText("Orbit Labs")).toBeVisible();
  await expect(page.getByText("Astranis")).toHaveCount(0);

  await page.getByLabel("Relevance").selectOption("ALL");
  await page.getByLabel("Sort").selectOption("newest_first");
  await page.getByRole("button", { name: "Mark Applied" }).first().click();
  await expect(page.getByText("Marked as applied.")).toBeVisible();

  await page.getByLabel("Recently added").check();
  await expect(page.getByText("Astranis")).toBeVisible();
});

test("persists detail-page recruiting edits and shows the relevance section", async ({ page }) => {
  await mockRecruitingRoutes(page);

  await page.goto("/jobs");
  await page.getByRole("link", { name: "Open Detail" }).first().click();
  await expect(page.getByRole("heading", { name: "Backend Intern" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Relevance" })).toBeVisible();
  await expect(page.getByText("Why this role is showing up")).toBeVisible();
  await expect(page.getByText("Match score 92 clears your 60 threshold.")).toBeVisible();

  await page.getByLabel("Workflow status").selectOption("INTERVIEW");
  await page.getByRole("textbox", { name: "Next action", exact: true }).fill("Prepare stories");
  await page.getByLabel("Next action due date").fill("2026-06-12");
  await page.getByLabel("Notes").fill("Need to review systems design fundamentals.");
  await page.getByRole("button", { name: "Save Recruiting Details" }).click();

  await expect(page.getByText("Recruiting details saved.")).toBeVisible();
  await expect(page.getByText("INTERVIEW", { exact: true })).toBeVisible();
  await expect(page.getByText("Prepare stories")).toBeVisible();
});

test("lets JP update recruiting preferences from the settings page", async ({ page }) => {
  await mockRecruitingRoutes(page);

  await page.goto("/preferences/recruiting");
  await expect(page.getByRole("heading", { name: "Recruiting Preferences" })).toBeVisible();

  await page.getByRole("button", { name: "Cloud" }).click();
  await page.getByLabel("Remote preference").selectOption("REMOTE");
  await page.getByLabel("Minimum match score").fill("70");
  await page.getByLabel("Excluded keywords").fill("clearance");
  await page.getByRole("button", { name: "Save Preferences" }).click();

  await expect(page.getByText("Preferences saved. Job relevance has been refreshed across the board.")).toBeVisible();
});
