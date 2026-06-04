"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { SectionCard } from "@/components/section-card";
import { getJobs, updateJob } from "@/lib/api";
import type { Job, JobsQuery, JobSort, JobWorkflowStatus, UpdateJobPayload } from "@/lib/types";

const WORKFLOW_OPTIONS: Array<{ value: "ALL" | JobWorkflowStatus; label: string }> = [
  { value: "ALL", label: "All statuses" },
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

const SORT_OPTIONS: Array<{ value: JobSort; label: string }> = [
  { value: "match_score_desc", label: "Match score: high to low" },
  { value: "match_score_asc", label: "Match score: low to high" },
  { value: "updated_at_desc", label: "Recently updated" },
  { value: "created_at_desc", label: "Recently added" },
  { value: "company_asc", label: "Company A-Z" },
];

function formatDate(value: string | null) {
  if (!value) {
    return null;
  }

  const normalizedValue = value.length <= 10 ? `${value}T00:00:00` : value;
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(normalizedValue));
}

function getStatusTone(status: JobWorkflowStatus) {
  switch (status) {
    case "OFFER":
      return "status-pill--success";
    case "INTERVIEW":
    case "FINAL_ROUND":
    case "OA":
      return "status-pill--accent";
    case "REJECTED":
    case "WITHDRAWN":
      return "status-pill--danger";
    case "APPLIED":
    case "SAVED":
      return "status-pill--warning";
    default:
      return "";
  }
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionJobId, setActionJobId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<"ALL" | JobWorkflowStatus>("ALL");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [sort, setSort] = useState<JobSort>("match_score_desc");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let isActive = true;
    const query: JobsQuery = {
      status: statusFilter === "ALL" ? undefined : [statusFilter],
      include_archived: includeArchived,
      sort,
    };

    async function fetchJobs() {
      try {
        const nextJobs = await getJobs(query);
        if (!isActive) {
          return;
        }
        setError(null);
        setJobs(nextJobs);
      } catch (loadError) {
        if (!isActive) {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Failed to load jobs.");
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void fetchJobs();

    return () => {
      isActive = false;
    };
  }, [statusFilter, includeArchived, sort, refreshKey]);

  function handleRetry() {
    setIsLoading(true);
    setRefreshKey((current) => current + 1);
  }

  async function handleQuickAction(jobId: string, payload: UpdateJobPayload, message: string) {
    try {
      setActionJobId(jobId);
      setError(null);
      setSuccess(null);
      const updatedJob = await updateJob(jobId, payload);
      setJobs((current) => {
        const nextJobs = current.map((job) => (job.id === jobId ? updatedJob : job));
        if (!includeArchived && updatedJob.is_archived) {
          return nextJobs.filter((job) => job.id !== jobId);
        }
        return nextJobs;
      });
      setSuccess(message);
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to update job.");
    } finally {
      setActionJobId(null);
    }
  }

  const metrics = {
    totalJobs: jobs.length,
    savedJobs: jobs.filter((job) => job.workflow_status === "SAVED").length,
    applicationsSubmitted: jobs.filter((job) =>
      ["APPLIED", "OA", "INTERVIEW", "FINAL_ROUND", "OFFER", "REJECTED", "WITHDRAWN"].includes(job.workflow_status),
    ).length,
    interviews: jobs.filter((job) => ["INTERVIEW", "FINAL_ROUND"].includes(job.workflow_status)).length,
    offers: jobs.filter((job) => job.workflow_status === "OFFER").length,
  };

  return (
    <div className="grid">
      <PageHeader
        title="Recruiting Dashboard"
        description="Triage internship roles, move them through your application workflow, and keep analysis context attached to each job."
        actions={
          <Link className="button" href="/jobs/new">
            Add Job
          </Link>
        }
      />

      {error ? (
        <div className="error-banner">
          <div>{error}</div>
          <button className="button button--secondary" onClick={handleRetry} type="button">
            Retry
          </button>
        </div>
      ) : null}
      {success ? <div className="success-banner">{success}</div> : null}

      <div className="stats-row stats-row--five">
        <div className="stat">
          <p className="stat__label">Total jobs</p>
          <p className="stat__value">{metrics.totalJobs}</p>
        </div>
        <div className="stat">
          <p className="stat__label">Saved jobs</p>
          <p className="stat__value">{metrics.savedJobs}</p>
        </div>
        <div className="stat">
          <p className="stat__label">Applications submitted</p>
          <p className="stat__value">{metrics.applicationsSubmitted}</p>
        </div>
        <div className="stat">
          <p className="stat__label">Interviews</p>
          <p className="stat__value">{metrics.interviews}</p>
        </div>
        <div className="stat">
          <p className="stat__label">Offers</p>
          <p className="stat__value">{metrics.offers}</p>
        </div>
      </div>

      <SectionCard
        title="Pipeline"
        description="Filter the dashboard by workflow status, decide whether to include archived roles, and sort by fit score."
      >
        <div className="dashboard-toolbar">
          <div className="field">
            <label htmlFor="statusFilter">Status</label>
            <select
              id="statusFilter"
              value={statusFilter}
              onChange={(event) => {
                setIsLoading(true);
                setStatusFilter(event.target.value as "ALL" | JobWorkflowStatus);
              }}
            >
              {WORKFLOW_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor="sortBy">Sort</label>
            <select
              id="sortBy"
              value={sort}
              onChange={(event) => {
                setIsLoading(true);
                setSort(event.target.value as JobSort);
              }}
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <label className="checkbox-field checkbox-field--toolbar">
            <input
              checked={includeArchived}
              type="checkbox"
              onChange={(event) => {
                setIsLoading(true);
                setIncludeArchived(event.target.checked);
              }}
            />
            <span>Include archived jobs</span>
          </label>
        </div>
      </SectionCard>

      <SectionCard
        title="Jobs"
        description="Each job keeps its workflow state, latest match summary, next step, and analysis history in one place."
      >
        {isLoading ? (
          <div className="loading-state">
            <div className="loading-card" />
            <div className="loading-card" />
          </div>
        ) : jobs.length ? (
          <div className="dashboard-job-list">
            {jobs.map((job) => {
              const isUpdating = actionJobId === job.id;

              return (
                <article className="dashboard-job-card" key={job.id}>
                  <div className="dashboard-job-card__header">
                    <div>
                      <div className="dashboard-job-card__pills">
                        <span className={`status-pill ${getStatusTone(job.workflow_status)}`}>{job.workflow_status}</span>
                        <span className="pill">{job.source_type}</span>
                        {job.latest_match_score !== null ? <span className="pill">Match {job.latest_match_score}</span> : null}
                      </div>
                      <h3 className="job-card__title">{job.title}</h3>
                      <div className="job-card__meta">
                        {job.company_name} • {job.location || "Location not provided"}
                      </div>
                    </div>

                    <Link className="button button--secondary" href={`/jobs/${job.id}`}>
                      Open Detail
                    </Link>
                  </div>

                  <div className="dashboard-job-card__details">
                    <div>
                      <span className="muted">Recommendation</span>
                      <p>{job.latest_recommendation ?? "No analysis yet"}</p>
                    </div>
                    <div>
                      <span className="muted">Applied</span>
                      <p>{formatDate(job.applied_date) ?? "Not yet"}</p>
                    </div>
                    <div>
                      <span className="muted">Next action</span>
                      <p>{job.next_action || "No next step set"}</p>
                    </div>
                    <div>
                      <span className="muted">Due</span>
                      <p>{formatDate(job.next_action_due_date) ?? "No due date"}</p>
                    </div>
                  </div>

                  <div className="job-card__skills">
                    {job.normalized_requirements.slice(0, 6).map((skill) => (
                      <span className="pill" key={`${job.id}-${skill}`}>
                        {skill}
                      </span>
                    ))}
                  </div>

                  <div className="dashboard-job-card__actions">
                    <button
                      className="button button--secondary"
                      disabled={isUpdating}
                      onClick={() => void handleQuickAction(job.id, { workflow_status: "SAVED" }, "Job saved.")}
                      type="button"
                    >
                      Save Job
                    </button>
                    <button
                      className="button button--secondary"
                      disabled={isUpdating}
                      onClick={() => void handleQuickAction(job.id, { workflow_status: "APPLIED" }, "Marked as applied.")}
                      type="button"
                    >
                      Mark Applied
                    </button>
                    <button
                      className="button button--secondary"
                      disabled={isUpdating}
                      onClick={() => void handleQuickAction(job.id, { workflow_status: "INTERVIEW" }, "Marked as interview.")}
                      type="button"
                    >
                      Mark Interview
                    </button>
                    <button
                      className="button button--secondary"
                      disabled={isUpdating}
                      onClick={() => void handleQuickAction(job.id, { workflow_status: "REJECTED" }, "Marked as rejected.")}
                      type="button"
                    >
                      Mark Rejected
                    </button>
                    <button
                      className="button button--secondary"
                      disabled={isUpdating}
                      onClick={() => void handleQuickAction(job.id, { is_archived: true }, "Job archived.")}
                      type="button"
                    >
                      Archive
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <div className="empty-state-panel">
            <p className="empty-state-title">No jobs match the current view</p>
            <p className="empty-state">Adjust the status or archive filters, or add a new job to continue building your pipeline.</p>
            <div>
              <Link className="button" href="/jobs/new">
                Add First Job
              </Link>
            </div>
          </div>
        )}
      </SectionCard>
    </div>
  );
}
