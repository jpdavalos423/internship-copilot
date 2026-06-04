"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { JobForm } from "@/components/job-form";
import { JobUrlForm } from "@/components/job-url-form";
import { PageHeader } from "@/components/page-header";
import { SectionCard } from "@/components/section-card";
import { createJob, ingestJobUrl } from "@/lib/api";

export default function NewJobPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"manual" | "url">("manual");
  const [form, setForm] = useState({
    company_name: "",
    title: "",
    location: "",
    raw_text: "",
  });
  const [jobUrl, setJobUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [validationErrors, setValidationErrors] = useState<
    Partial<Record<"company_name" | "title" | "location" | "raw_text", string>>
  >({});
  const [urlValidationError, setUrlValidationError] = useState<string | null>(null);

  function validateForm() {
    const nextErrors: Partial<Record<"company_name" | "title" | "location" | "raw_text", string>> = {};

    if (!form.company_name.trim()) {
      nextErrors.company_name = "Company is required.";
    }
    if (!form.title.trim()) {
      nextErrors.title = "Title is required.";
    }
    if (!form.raw_text.trim()) {
      nextErrors.raw_text = "Raw job text is required.";
    }

    setValidationErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  function validateJobUrl() {
    if (!jobUrl.trim()) {
      setUrlValidationError("Job posting URL is required.");
      return false;
    }

    setUrlValidationError(null);
    return true;
  }

  async function handleManualSubmit() {
    if (!validateForm()) {
      return;
    }

    setIsSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const job = await createJob({
        ...form,
        company_name: form.company_name.trim(),
        title: form.title.trim(),
        location: form.location.trim(),
        raw_text: form.raw_text.trim(),
      });
      setSuccess("Job created successfully. Redirecting to the detail page...");
      router.push(`/jobs/${job.id}?created=1`);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Failed to create job.");
      setIsSaving(false);
    }
  }

  async function handleUrlSubmit() {
    if (!validateJobUrl()) {
      return;
    }

    setIsSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await ingestJobUrl({ url: jobUrl.trim() });
      const search = result.created ? "created=1" : "duplicate=1";
      setSuccess(
        result.created
          ? "Job ingested successfully. Redirecting to the detail page..."
          : "Job already exists. Redirecting to the saved record...",
      );
      router.push(`/jobs/${result.job.id}?${search}`);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Failed to ingest job URL.");
      setIsSaving(false);
    }
  }

  return (
    <div className="grid">
      <PageHeader
        title="Add Job"
        description="Create a job either by pasting the full text manually or by ingesting a single job posting URL."
      />

      {error ? <div className="error-banner">{error}</div> : null}
      {success ? <div className="success-banner">{success}</div> : null}
      <div className="info-banner">
        Manual creation still works, and URL ingestion currently supports one job posting at a time.
      </div>

      <SectionCard
        title="New Job"
        description="Choose manual entry when you already have the text, or use a job posting URL to ingest it automatically."
      >
        <div className="segmented-control" role="tablist" aria-label="Job creation mode">
          <button
            aria-selected={mode === "manual"}
            className={`segmented-control__button${mode === "manual" ? " segmented-control__button--active" : ""}`}
            onClick={() => setMode("manual")}
            role="tab"
            type="button"
          >
            Paste Job Text
          </button>
          <button
            aria-selected={mode === "url"}
            className={`segmented-control__button${mode === "url" ? " segmented-control__button--active" : ""}`}
            onClick={() => setMode("url")}
            role="tab"
            type="button"
          >
            Paste Job URL
          </button>
        </div>

        {mode === "manual" ? (
          <JobForm
            form={form}
            isSaving={isSaving}
            validationErrors={validationErrors}
            onChange={setForm}
            onSubmit={handleManualSubmit}
          />
        ) : (
          <JobUrlForm
            isSaving={isSaving}
            onChange={setJobUrl}
            onSubmit={handleUrlSubmit}
            url={jobUrl}
            validationError={urlValidationError ?? undefined}
          />
        )}
      </SectionCard>
    </div>
  );
}
