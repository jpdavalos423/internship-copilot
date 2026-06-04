"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { JobForm } from "@/components/job-form";
import { PageHeader } from "@/components/page-header";
import { SectionCard } from "@/components/section-card";
import { createJob } from "@/lib/api";

export default function NewJobPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    company_name: "",
    title: "",
    location: "",
    raw_text: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [validationErrors, setValidationErrors] = useState<
    Partial<Record<"company_name" | "title" | "location" | "raw_text", string>>
  >({});

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

  async function handleSubmit() {
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

  return (
    <div className="grid">
      <PageHeader
        title="Add Job"
        description="Paste the role details exactly as posted so the backend parser can extract required and preferred skills deterministically."
      />

      {error ? <div className="error-banner">{error}</div> : null}
      {success ? <div className="success-banner">{success}</div> : null}
      <div className="info-banner">
        Required fields for Phase 0 are company, title, and raw job text. Location can be left blank.
      </div>

      <SectionCard title="New Job" description="Only four fields are required for the current Phase 0 workflow.">
        <JobForm
          form={form}
          isSaving={isSaving}
          validationErrors={validationErrors}
          onChange={setForm}
          onSubmit={handleSubmit}
        />
      </SectionCard>
    </div>
  );
}
