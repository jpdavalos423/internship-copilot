"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { SectionCard } from "@/components/section-card";
import { getJobs, updateJob } from "@/lib/api";
import type {
  Job,
  JobRelevance,
  JobsQuery,
  JobSort,
  JobWorkflowStatus,
  UpdateJobPayload,
} from "@/lib/types";

const VIEW_OPTIONS: Array<{ value: "relevant" | "all"; label: string }> = [
  { value: "relevant", label: "Relevant Jobs" },
  { value: "all", label: "All Jobs" },
];

const RELEVANCE_OPTIONS: Array<{ value: "ALL" | JobRelevance; label: string }> = [
  { value: "ALL", label: "All relevance" },
  { value: "HIGHLY_RELEVANT", label: "Highly relevant" },
  { value: "RELEVANT", label: "Relevant" },
  { value: "REVIEW", label: "Review" },
  { value: "NOT_RELEVANT", label: "Not relevant" },
];

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
  { value: "newest_first", label: "Newest first" },
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

function getRelevanceTone(relevance: JobRelevance) {
  switch (relevance) {
    case "HIGHLY_RELEVANT":
      return "relevance-pill relevance-pill--high";
    case "RELEVANT":
      return "relevance-pill relevance-pill--relevant";
    case "REVIEW":
      return "relevance-pill relevance-pill--review";
    default:
      return "relevance-pill relevance-pill--muted";
  }
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionJobId, setActionJobId] = useState<string | null>(null);
  const [view, setView] = useState<"relevant" | "all">("relevant");
  const [relevanceFilter, setRelevanceFilter] = useState<"ALL" | JobRelevance>("ALL");
  const [statusFilter, setStatusFilter] = useState<"ALL" | JobWorkflowStatus>("ALL");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [hideNotRelevant, setHideNotRelevant] = useState(true);
  const [recentlyAddedOnly, setRecentlyAddedOnly] = useState(false);
  const [sort, setSort] = useState<JobSort>("match_score_desc");
  const [refreshKey, setRefreshKey] = useState(0);
  const [boardLoadedAt] = useState(() => Date.now());

  useEffect(() => {
    let isActive = true;
    const query: JobsQuery = {
      view,
      relevance: relevanceFilter === "ALL" ? undefined : [relevanceFilter],
      status: statusFilter === "ALL" ? undefined : [statusFilter],
      hide_not_relevant: hideNotRelevant,
      recently_added: recentlyAddedOnly,
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
  }, [view, relevanceFilter, statusFilter, hideNotRelevant, recentlyAddedOnly, includeArchived, sort, refreshKey]);

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
    highlyRelevant: jobs.filter((job) => job.relevance === "HIGHLY_RELEVANT").length,
    relevant: jobs.filter((job) => job.relevance === "RELEVANT").length,
    review: jobs.filter((job) => job.relevance === "REVIEW").length,
    recentlyAdded: jobs.filter((job) => {
      const createdAt = new Date(job.created_at).getTime();
      return boardLoadedAt - createdAt <= 7 * 24 * 60 * 60 * 1000;
    }).length,
    applied: jobs.filter((job) =>
      ["APPLIED", "OA", "INTERVIEW", "FINAL_ROUND", "OFFER", "REJECTED", "WITHDRAWN"].includes(job.workflow_status),
    ).length,
  };

  return (
    <div className="grid">
      <PageHeader
        title="Personalized Job Board"
        description="Review the internships that best fit JP's recruiting goals while keeping workflow status and analysis history intact."
        actions={
          <>
            <Link className="button button--secondary" href="/preferences/recruiting">
              Preferences
            </Link>
            <Link className="button" href="/jobs/new">
              Add Job
            </Link>
          </>
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
          <p className="stat__label">Highly relevant</p>
          <p className="stat__value">{metrics.highlyRelevant}</p>
        </div>
        <div className="stat">
          <p className="stat__label">Relevant</p>
          <p className="stat__value">{metrics.relevant}</p>
        </div>
        <div className="stat">
          <p className="stat__label">Need review</p>
          <p className="stat__value">{metrics.review}</p>
        </div>
        <div className="stat">
          <p className="stat__label">Recently added</p>
          <p className="stat__value">{metrics.recentlyAdded}</p>
        </div>
        <div className="stat">
          <p className="stat__label">Applied+</p>
          <p className="stat__value">{metrics.applied}</p>
        </div>
      </div>

      <SectionCard
        title="Board Controls"
        description="Switch between your strict relevant queue and the full inventory, then refine by relevance, workflow stage, and freshness."
      >
        <div className="grid">
          <div className="segmented-control">
            {VIEW_OPTIONS.map((option) => (
              <button
                className={`segmented-control__button${view === option.value ? " segmented-control__button--active" : ""}`}
                key={option.value}
                onClick={() => {
                  setIsLoading(true);
                  setView(option.value);
                  setHideNotRelevant(option.value === "relevant");
                }}
                type="button"
              >
                {option.label}
              </button>
            ))}
          </div>

          <div className="dashboard-toolbar">
            <div className="field">
              <label htmlFor="relevanceFilter">Relevance</label>
              <select
                id="relevanceFilter"
                value={relevanceFilter}
                onChange={(event) => {
                  setIsLoading(true);
                  setRelevanceFilter(event.target.value as "ALL" | JobRelevance);
                }}
              >
                {RELEVANCE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="field">
              <label htmlFor="statusFilter">Workflow status</label>
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
                checked={hideNotRelevant}
                type="checkbox"
                onChange={(event) => {
                  setIsLoading(true);
                  setHideNotRelevant(event.target.checked);
                }}
              />
              <span>Hide not-relevant jobs</span>
            </label>

            <label className="checkbox-field checkbox-field--toolbar">
              <input
                checked={recentlyAddedOnly}
                type="checkbox"
                onChange={(event) => {
                  setIsLoading(true);
                  setRecentlyAddedOnly(event.target.checked);
                }}
              />
              <span>Recently added</span>
            </label>

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
        </div>
      </SectionCard>

      <SectionCard
        title={view === "relevant" ? "Relevant Jobs" : "All Jobs"}
        description="Each card shows the job's relevance verdict, why it landed there, and its separate recruiting workflow status."
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
              const primaryReason = job.relevance_reasons[0] ?? "Visible for manual review.";

              return (
                <article className="dashboard-job-card" key={job.id}>
                  <div className="dashboard-job-card__header">
                    <div>
                      <div className="dashboard-job-card__pills">
                        <span className={getRelevanceTone(job.relevance)}>{job.relevance.replaceAll("_", " ")}</span>
                        <span className={`status-pill ${getStatusTone(job.workflow_status)}`}>{job.workflow_status}</span>
                        <span className="pill">{job.source_type}</span>
                        {job.relevance_score !== null ? <span className="pill">Relevance {job.relevance_score}</span> : null}
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

                  <div className="job-card__reasoning">
                    <p className="job-card__reason">{primaryReason}</p>
                    {job.relevance_flags[0] ? <p className="muted">Watchout: {job.relevance_flags[0]}</p> : null}
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
                      <span className="muted">Added</span>
                      <p>{formatDate(job.created_at) ?? "Unknown"}</p>
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
                      onClick={() =>
                        void handleQuickAction(job.id, { workflow_status: "INTERVIEW" }, "Marked as interview.")
                      }
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
            <p className="empty-state-title">No jobs match the current board view</p>
            <p className="empty-state">
              Adjust the relevance, workflow, archive, or recently added filters, or add a new job to keep building the board.
            </p>
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
