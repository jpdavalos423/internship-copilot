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
  created_at: string;
  updated_at: string;
  latest_match_score: number | null;
  latest_recommendation: string | null;
  latest_match_report_id: string | null;
  latest_analysis_created_at: string | null;
};

const baseJob = {
  raw_text: "Requirements\nPython\nREST APIs",
  source_url: null,
  external_id: null,
  content_hash: null,
  last_seen_at: null,
  is_hidden: false,
  normalized_requirements: ["python", "rest apis"],
  normalized_preferred: ["aws"],
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
      is_archived: true,
      is_saved: true,
      latest_match_score: 55,
      latest_recommendation: "LOW_PRIORITY",
    },
  ];

  await page.route("**/api/v1/jobs?**", async (route) => {
    if (route.request().method() !== "GET") {
      await route.fallback();
      return;
    }

    const url = new URL(route.request().url());
    const statusFilter = url.searchParams.get("status");
    const includeArchived = url.searchParams.get("include_archived") === "true";
    const sort = url.searchParams.get("sort") ?? "match_score_desc";

    let result = jobs.filter((job) => includeArchived || !job.is_archived);

    if (statusFilter) {
      const statuses = statusFilter.split(",");
      result = result.filter((job) => statuses.includes(job.workflow_status));
    }

    result = [...result].sort((left, right) => {
      const leftScore = left.latest_match_score ?? -1;
      const rightScore = right.latest_match_score ?? -1;
      if (sort === "match_score_asc") {
        return leftScore - rightScore;
      }
      return rightScore - leftScore;
    });

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(result),
    });
  });

  await page.route("**/api/v1/jobs", async (route) => {
    if (route.request().method() === "GET") {
      const result = jobs.filter((job) => !job.is_archived).sort((left, right) => {
        const leftScore = left.latest_match_score ?? -1;
        const rightScore = right.latest_match_score ?? -1;
        return rightScore - leftScore;
      });

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(result),
      });
      return;
    }

    await route.fallback();
  });

  await page.route("**/api/v1/jobs/*", async (route) => {
    const url = new URL(route.request().url());
    const jobId = url.pathname.split("/").pop();
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

test("shows recruiting metrics, supports status filtering, and allows quick actions", async ({ page }) => {
  await mockRecruitingRoutes(page);

  await page.goto("/jobs");

  await expect(page.getByRole("heading", { name: "Recruiting Dashboard" })).toBeVisible();
  await expect(page.getByText("Total jobs").locator("..")).toContainText("2");
  await expect(page.getByText("Saved jobs").locator("..")).toContainText("1");
  await expect(page.getByText("Astranis")).toBeVisible();
  await expect(page.getByText("Orbit Labs")).toBeVisible();

  await page.getByLabel("Status").selectOption("DISCOVERED");
  await expect(page.getByText("Orbit Labs")).toBeVisible();
  await expect(page.getByText("Astranis")).toHaveCount(0);

  await page.getByRole("button", { name: "Mark Applied" }).click();
  await expect(page.getByText("Marked as applied.")).toBeVisible();

  await page.getByLabel("Status").selectOption("ALL");
  await page.getByLabel("Include archived jobs").check();
  await expect(page.getByText("Pine AI")).toBeVisible();
});

test("sorts by match score and persists detail-page recruiting edits", async ({ page }) => {
  await mockRecruitingRoutes(page);

  await page.goto("/jobs");
  await page.getByLabel("Sort").selectOption("match_score_asc");

  const titles = page.locator(".job-card__title");
  await expect(titles.nth(0)).toHaveText("Platform Intern");
  await expect(titles.nth(1)).toHaveText("Backend Intern");

  await page.getByRole("link", { name: "Open Detail" }).first().click();
  await expect(page.getByRole("heading", { name: "Platform Intern" })).toBeVisible();

  await page.getByLabel("Workflow status").selectOption("INTERVIEW");
  await page.getByRole("textbox", { name: "Next action", exact: true }).fill("Prepare stories");
  await page.getByLabel("Next action due date").fill("2026-06-12");
  await page.getByLabel("Notes").fill("Need to review systems design fundamentals.");
  await page.getByRole("button", { name: "Save Recruiting Details" }).click();

  await expect(page.getByText("Recruiting details saved.")).toBeVisible();
  await expect(page.getByText("INTERVIEW", { exact: true })).toBeVisible();
  await expect(page.getByText("Prepare stories")).toBeVisible();

  await page.reload();
  await expect(page.getByLabel("Workflow status")).toHaveValue("INTERVIEW");
  await expect(page.getByRole("textbox", { name: "Next action", exact: true })).toHaveValue("Prepare stories");
  await expect(page.getByLabel("Notes")).toHaveValue("Need to review systems design fundamentals.");
});
