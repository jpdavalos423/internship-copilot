"use client";

import { useState } from "react";
import { SectionCard } from "@/components/section-card";
import { updateJob } from "@/lib/api";
import type { Job, JobWorkflowStatus, UpdateJobPayload } from "@/lib/types";

const WORKFLOW_OPTIONS: Array<{ value: JobWorkflowStatus; label: string }> = [
  { value: "DISCOVERED", label: "Discovered" },
  { value: "SAVED", label: "Saved" },
  { value: "APPLIED", label: "Applied" },
  { value: "OA", label: "OA" },
  { value: "INTERVIEW", label: "Interview" },
  { value: "FINAL_ROUND", label: "Final Round" },
  { value: "OFFER", label: "Offer" },
  { value: "REJECTED", label: "Rejected" },
  { value: "WITHDRAWN", label: "Withdrawn" },
];

type JobRecruitingEditorProps = {
  job: Job;
  onJobUpdated: (job: Job, message: string) => void;
};

export function JobRecruitingEditor({ job, onJobUpdated }: JobRecruitingEditorProps) {
  const [form, setForm] = useState({
    workflow_status: job.workflow_status,
    applied_date: job.applied_date ?? "",
    next_action: job.next_action,
    next_action_due_date: job.next_action_due_date ?? "",
    notes: job.notes,
    is_archived: job.is_archived,
  });
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateField<Key extends keyof typeof form>(key: Key, value: (typeof form)[Key]) {
    setForm((current) => ({
      ...current,
      [key]: value,
    }));
  }

  async function handleSave() {
    try {
      setIsSaving(true);
      setError(null);
      const payload: UpdateJobPayload = {
        workflow_status: form.workflow_status,
        applied_date: form.applied_date || null,
        next_action: form.next_action.trim(),
        next_action_due_date: form.next_action_due_date || null,
        notes: form.notes.trim(),
        is_archived: form.is_archived,
      };
      const updatedJob = await updateJob(job.id, payload);
      onJobUpdated(updatedJob, "Recruiting details saved.");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Failed to save recruiting details.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <SectionCard
      title="Recruiting Workflow"
      description="Track where this role stands in your application pipeline and keep the next step visible."
    >
      <div className="grid">
        {error ? <div className="error-banner">{error}</div> : null}

        <div className="form__row">
          <div className="field">
            <label htmlFor="workflowStatus">Workflow status</label>
            <select
              id="workflowStatus"
              value={form.workflow_status}
              onChange={(event) => updateField("workflow_status", event.target.value as JobWorkflowStatus)}
            >
              {WORKFLOW_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor="appliedDate">Applied date</label>
            <input
              id="appliedDate"
              type="date"
              value={form.applied_date}
              onChange={(event) => updateField("applied_date", event.target.value)}
            />
          </div>
        </div>

        <div className="form__row">
          <div className="field">
            <label htmlFor="nextAction">Next action</label>
            <input
              id="nextAction"
              type="text"
              value={form.next_action}
              onChange={(event) => updateField("next_action", event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="nextActionDueDate">Next action due date</label>
            <input
              id="nextActionDueDate"
              type="date"
              value={form.next_action_due_date}
              onChange={(event) => updateField("next_action_due_date", event.target.value)}
            />
          </div>
        </div>

        <div className="field">
          <label htmlFor="jobNotes">Notes</label>
          <textarea
            id="jobNotes"
            value={form.notes}
            onChange={(event) => updateField("notes", event.target.value)}
          />
        </div>

        <label className="checkbox-field">
          <input
            checked={form.is_archived}
            type="checkbox"
            onChange={(event) => updateField("is_archived", event.target.checked)}
          />
          <span>Archive this job from the default dashboard view</span>
        </label>

        <div>
          <button className="button" disabled={isSaving} onClick={() => void handleSave()} type="button">
            {isSaving ? "Saving..." : "Save Recruiting Details"}
          </button>
        </div>
      </div>
    </SectionCard>
  );
}
