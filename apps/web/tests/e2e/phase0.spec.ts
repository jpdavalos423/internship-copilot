import fs from "node:fs";
import path from "node:path";
import { expect, test, type Page } from "@playwright/test";

const repoRoot = path.resolve(__dirname, "../../../..");
const sampleResume = fs.readFileSync(path.join(repoRoot, "data/samples/sample_resume.txt"), "utf8");
const sampleJob = fs.readFileSync(path.join(repoRoot, "data/samples/sample_job_backend.txt"), "utf8");

test.describe.configure({ mode: "serial" });

async function goToPrimaryNav(page: Page, label: "Profile" | "Jobs") {
  const primaryNavigation = page.getByRole("navigation", { name: "Primary navigation" });
  await primaryNavigation.getByRole("link", { name: label, exact: true }).click();
}

async function saveSampleProfile(page: Page) {
  await page.goto("/profile");
  await page.getByLabel("Resume text").fill(sampleResume);
  await page.getByRole("button", { name: "Save Profile" }).click();
  await expect(page.getByText("Profile saved successfully.")).toBeVisible();
}

async function createSampleJob(page: Page, suffix: string) {
  await page.goto("/jobs/new");
  await page.getByLabel("Company").fill(`Astranis ${suffix}`);
  await page.getByLabel("Title").fill("Backend Software Engineer Intern");
  await page.getByLabel("Location").fill("San Francisco, CA");
  await page.getByLabel("Raw job text").fill(sampleJob);
  await page.getByRole("button", { name: "Create Job" }).click();
  await expect(page).toHaveURL(/\/jobs\/[0-9a-f-]+\?created=1$/);
  await expect(page.getByText("Job created successfully.")).toBeVisible();
}

async function runAnalysisAndVerify(page: Page) {
  await page.getByRole("button", { name: "Run Analysis" }).click();

  await expect(page.getByRole("heading", { name: "Analysis Summary" })).toBeVisible();
  await expect(page.getByText("Match Score")).toBeVisible();
  await expect(page.locator(".analysis-score")).not.toBeEmpty();
  await expect(page.getByText("Recommendation")).toBeVisible();
  await expect(page.locator(".recommendation-badge")).not.toBeEmpty();

  const strengthsSection = page.locator("section.card", {
    has: page.getByRole("heading", { name: "Strengths" }),
  });
  await expect(strengthsSection.getByRole("listitem").first()).toBeVisible();

  const missingKeywordsSection = page.locator("section.card", {
    has: page.getByRole("heading", { name: "Missing Keywords" }),
  });
  await expect(missingKeywordsSection.locator(".pill").first()).toBeVisible();

  await expect(page.getByRole("heading", { name: "Application Answers" })).toBeVisible();
  await expect(page.getByText("Not generated yet").first()).toBeVisible();
}

test("shows client-side validation for empty profile and job forms", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Phase 0 Dashboard" })).toBeVisible();

  await goToPrimaryNav(page, "Profile");
  await expect(page).toHaveURL(/\/profile$/);
  await page.getByRole("button", { name: "Save Profile" }).click();
  await expect(page.getByText("Resume text is required before you can save the profile.")).toBeVisible();

  await goToPrimaryNav(page, "Jobs");
  await expect(page).toHaveURL(/\/jobs$/);
  await page.getByRole("link", { name: "Add Job" }).click();
  await expect(page).toHaveURL(/\/jobs\/new$/);

  await page.getByRole("button", { name: "Create Job" }).click();
  await expect(page.getByText("Company is required.")).toBeVisible();
  await expect(page.getByText("Title is required.")).toBeVisible();
  await expect(page.getByText("Raw job text is required.")).toBeVisible();
});

test("requires a saved profile before analysis can run", async ({ page }) => {
  await createSampleJob(page, "No Profile");
  await page.getByRole("button", { name: "Run Analysis" }).click();

  await expect(page.getByText("Candidate profile is required before analysis")).toBeVisible();
  await expect(page.getByText("No analysis has been run yet for this job.")).toHaveCount(0);
});

test("shows quiet empty states before a profile or analysis exists", async ({ page }) => {
  await page.goto("/profile");
  await expect(page.getByText("No profile is saved yet.")).toBeVisible();
  await expect(page.getByText("Candidate profile not found")).toHaveCount(0);

  await createSampleJob(page, "No Analysis Yet");
  await expect(page.getByText("No analysis has been run yet for this job.")).toBeVisible();
  await expect(page.getByText("Match report not found")).toHaveCount(0);
  await expect(page.getByText("Run analysis first")).toBeVisible();
});

test("Phase 0 workflow saves a profile, creates a job, and runs analysis", async ({ page }) => {
  await test.step("Open homepage and save the sample profile", async () => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Phase 0 Dashboard" })).toBeVisible();

    await goToPrimaryNav(page, "Profile");
    await expect(page).toHaveURL(/\/profile$/);

    await page.getByLabel("Resume text").fill(sampleResume);
    await page.getByRole("button", { name: "Save Profile" }).click();

    await expect(page.getByText("Profile saved successfully.")).toBeVisible();
  });

  await test.step("Navigate to the new job flow and create a sample job", async () => {
    await goToPrimaryNav(page, "Jobs");
    await expect(page).toHaveURL(/\/jobs$/);

    await page.getByRole("link", { name: "Add Job" }).click();
    await expect(page).toHaveURL(/\/jobs\/new$/);

    await page.getByLabel("Company").fill("Astranis");
    await page.getByLabel("Title").fill("Backend Software Engineer Intern");
    await page.getByLabel("Location").fill("San Francisco, CA");
    await page.getByLabel("Raw job text").fill(sampleJob);
    await page.getByRole("button", { name: "Create Job" }).click();

    await expect(page).toHaveURL(/\/jobs\/[0-9a-f-]+\?created=1$/);
    await expect(page.getByText("Job created successfully.")).toBeVisible();
  });

  await test.step("Run analysis and verify the report renders", async () => {
    await runAnalysisAndVerify(page);
  });
});

test("persists saved profile and analysis results across reloads", async ({ page }) => {
  await saveSampleProfile(page);

  await expect(page.locator(".pill-list .pill").first()).toBeVisible();
  await page.reload();
  await expect(page.getByLabel("Resume text")).toHaveValue(sampleResume.trim());
  await expect(page.locator(".pill-list .pill").first()).toBeVisible();

  await createSampleJob(page, "Persistence");
  await runAnalysisAndVerify(page);

  await page.reload();
  await expect(page.getByRole("heading", { name: "Analysis Summary" })).toBeVisible();
  await expect(page.locator(".analysis-score")).not.toBeEmpty();
  await expect(page.locator(".recommendation-badge")).not.toBeEmpty();
  await expect(page.getByText("Match report not found")).toHaveCount(0);
});

test("generates and persists application answers only when requested", async ({ page }) => {
  await saveSampleProfile(page);
  await createSampleJob(page, "Answers");
  await runAnalysisAndVerify(page);

  await expect(page.getByText("Not generated yet")).toHaveCount(5);
  await page.getByRole("button", { name: "Generate" }).first().click();

  await expect(page.getByText("Why This Company generated successfully.")).toBeVisible();
  await expect(page.getByText("Not generated yet")).toHaveCount(4);
  await expect(page.getByText("Saved for report")).toBeVisible();
  await expect(page.getByRole("button", { name: "Regenerate" }).first()).toBeVisible();

  await page.reload();
  await expect(page.getByText("Why This Company generated successfully.")).toHaveCount(0);
  await expect(page.getByText("Not generated yet")).toHaveCount(4);
  await expect(page.getByRole("button", { name: "Regenerate" }).first()).toBeVisible();
});
