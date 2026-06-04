import { expect, test, type Page } from "@playwright/test";

const mockJob = {
  id: "11111111-1111-1111-1111-111111111111",
  company_name: "Orbit Labs",
  title: "Backend Software Engineer Intern",
  location: "San Francisco, CA",
  raw_text: "Requirements\nPython\nREST APIs\n\nPreferred Qualifications\nAWS",
  source_type: "GREENHOUSE",
  source_url: "https://boards.greenhouse.io/orbitlabs/jobs/gh-12345",
  external_id: "gh-12345",
  content_hash: "abc123",
  last_seen_at: "2026-06-04T20:30:00Z",
  ingestion_status: "INGESTED",
  is_archived: false,
  is_hidden: false,
  is_saved: false,
  normalized_requirements: ["python", "rest apis"],
  normalized_preferred: ["aws"],
  created_at: "2026-06-04T20:30:00Z",
  updated_at: "2026-06-04T20:30:00Z",
};

async function mockJobDetailRoutes(page: Page) {
  await page.route("**/api/v1/jobs/11111111-1111-1111-1111-111111111111", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockJob),
    });
  });

  await page.route("**/api/v1/jobs/11111111-1111-1111-1111-111111111111/analysis", async (route) => {
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

test("ingests a job URL and shows source metadata on the detail page", async ({ page }) => {
  await mockJobDetailRoutes(page);

  await page.route("**/api/v1/jobs/ingest-url", async (route) => {
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify(mockJob),
    });
  });

  await page.goto("/jobs/new");
  await page.getByRole("tab", { name: "Paste Job URL" }).click();
  await page.getByLabel("Job posting URL").fill(mockJob.source_url);
  await page.getByRole("button", { name: "Ingest Job" }).click();

  await expect(page).toHaveURL(/\/jobs\/11111111-1111-1111-1111-111111111111\?created=1$/);
  await expect(page.getByText("Job created successfully.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Source", exact: true })).toBeVisible();
  await expect(page.getByText("GREENHOUSE", { exact: true })).toBeVisible();
  await expect(page.getByText("gh-12345", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: mockJob.source_url })).toBeVisible();
});

test("opens the existing job when URL ingestion returns a duplicate", async ({ page }) => {
  await mockJobDetailRoutes(page);

  await page.route("**/api/v1/jobs/ingest-url", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockJob),
    });
  });

  await page.goto("/jobs/new");
  await page.getByRole("tab", { name: "Paste Job URL" }).click();
  await page.getByLabel("Job posting URL").fill(mockJob.source_url);
  await page.getByRole("button", { name: "Ingest Job" }).click();

  await expect(page).toHaveURL(/\/jobs\/11111111-1111-1111-1111-111111111111\?duplicate=1$/);
  await expect(page.getByText("This job was already saved, so the existing record was opened.")).toBeVisible();
});

test("shows URL mode validation and backend ingestion errors inline", async ({ page }) => {
  await page.goto("/jobs/new");
  await page.getByRole("tab", { name: "Paste Job URL" }).click();
  await page.getByRole("button", { name: "Ingest Job" }).click();
  await expect(page.getByText("Job posting URL is required.")).toBeVisible();

  await page.route("**/api/v1/jobs/ingest-url", async (route) => {
    await route.fulfill({
      status: 422,
      contentType: "application/json",
      body: JSON.stringify({
        error: {
          code: "JOB_EXTRACTION_FAILED",
          message: "The job page did not contain enough structured information to create a job record.",
        },
      }),
    });
  });

  await page.getByLabel("Job posting URL").fill("https://example.com/jobs/unknown");
  await page.getByRole("button", { name: "Ingest Job" }).click();
  await expect(
    page.getByText("The job page did not contain enough structured information to create a job record."),
  ).toBeVisible();
});
