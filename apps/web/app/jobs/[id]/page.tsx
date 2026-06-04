"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { AnalysisPanel } from "@/components/analysis-panel";
import { ApplicationAnswersPanel } from "@/components/application-answers-panel";
import { JobRecruitingEditor } from "@/components/job-recruiting-editor";
import { PageHeader } from "@/components/page-header";
import { SectionCard } from "@/components/section-card";
import { analyzeJob, getJob, getLatestJobAnalysis, updateJob } from "@/lib/api";
import type { Job, MatchReport } from "@/lib/types";

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const jobId = params.id;
  const createdMessage = searchParams.get("created") === "1";
  const duplicateMessage = searchParams.get("duplicate") === "1";

  const [job, setJob] = useState<Job | null>(null);
  const [analysis, setAnalysis] = useState<MatchReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const loadedJobIdRef = useRef<string | null>(null);
  const bannerMessage = createdMessage
    ? "Job created successfully. Review the parsed skills below, then run analysis."
    : duplicateMessage
      ? "This job was already saved, so the existing record was opened."
      : success;

  async function loadJobAndAnalysis() {
    try {
      setIsLoading(true);
      setError(null);
      setAnalysisError(null);
      const loadedJob = await getJob(jobId);
      setJob(loadedJob);
      setAnalysis(await getLatestJobAnalysis(jobId));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load job.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (loadedJobIdRef.current === jobId) {
      return;
    }
    loadedJobIdRef.current = jobId;

    async function initialLoad() {
      try {
        setIsLoading(true);
        setError(null);
        setAnalysisError(null);
        const loadedJob = await getJob(jobId);
        setJob(loadedJob);
        setAnalysis(await getLatestJobAnalysis(jobId));
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Failed to load job.");
      } finally {
        setIsLoading(false);
      }
    }

    void initialLoad();
  }, [jobId]);

  async function handleAnalyze() {
    setIsAnalyzing(true);
    setAnalysisError(null);
    setSuccess(null);

    try {
      const nextAnalysis = await analyzeJob(jobId);
      setAnalysis(nextAnalysis);
      setSuccess("Analysis completed successfully. The report below reflects the latest deterministic scoring run.");
    } catch (runError) {
      setAnalysisError(runError instanceof Error ? runError.message : "Failed to run analysis.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handleQuickStatusUpdate(workflowStatus: Job["workflow_status"], message: string) {
    try {
      setAnalysisError(null);
      setSuccess(null);
      const updatedJob = await updateJob(jobId, { workflow_status: workflowStatus });
      setJob(updatedJob);
      setSuccess(message);
    } catch (updateError) {
      setAnalysisError(updateError instanceof Error ? updateError.message : "Failed to update job.");
    }
  }

  if (isLoading) {
    return (
      <div className="grid">
        <div className="loading-card loading-card--hero" />
        <div className="split-panel">
          <div className="loading-card" />
          <div className="loading-card" />
        </div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="error-banner">
        <div>{error ?? "Job not found."}</div>
        <button className="button button--secondary" onClick={() => void loadJobAndAnalysis()} type="button">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="grid">
      <PageHeader
        title={job.title}
        description={`${job.company_name} • ${job.location || "Location not provided"}`}
        actions={
          <>
            <button className="button button--secondary" onClick={() => void handleQuickStatusUpdate("SAVED", "Job saved.")} type="button">
              Save Job
            </button>
            <button
              className="button button--secondary"
              onClick={() => void handleQuickStatusUpdate("INTERVIEW", "Marked as interview.")}
              type="button"
            >
              Mark Interview
            </button>
            <button className="button" disabled={isAnalyzing} onClick={handleAnalyze} type="button">
              {isAnalyzing ? "Running Analysis..." : "Run Analysis"}
            </button>
          </>
        }
      />

      {bannerMessage ? <div className="success-banner">{bannerMessage}</div> : null}
      {analysisError ? <div className="error-banner">{analysisError}</div> : null}
      {!analysis && !analysisError ? (
        <div className="info-banner">
          No analysis has been run yet for this job. Use the Run Analysis button to generate the first report.
        </div>
      ) : null}

      <JobRecruitingEditor
        key={`${job.id}-${job.updated_at}-${job.workflow_status}-${job.applied_date ?? ""}-${job.next_action_due_date ?? ""}`}
        job={job}
        onJobUpdated={(updatedJob, message) => {
          setJob(updatedJob);
          setSuccess(message);
        }}
      />

      <div className="split-panel">
        <SectionCard title="Job Metadata" description="Normalized skills are parsed and persisted by the Django backend.">
          <div className="grid">
            <div className="metadata-grid">
              <div>
                <h3 className="card__title">Workflow Status</h3>
                <p className="muted">{job.workflow_status}</p>
              </div>
              <div>
                <h3 className="card__title">Source</h3>
                <p className="muted">{job.source_type}</p>
              </div>
              <div>
                <h3 className="card__title">Ingestion Status</h3>
                <p className="muted">{job.ingestion_status}</p>
              </div>
              <div>
                <h3 className="card__title">Applied Date</h3>
                <p className="muted">{job.applied_date ?? "Not applied yet"}</p>
              </div>
              <div>
                <h3 className="card__title">External ID</h3>
                <p className="muted">{job.external_id ?? "Not available"}</p>
              </div>
              <div>
                <h3 className="card__title">Source URL</h3>
                {job.source_url ? (
                  <a className="link link--inline" href={job.source_url} rel="noreferrer" target="_blank">
                    {job.source_url}
                  </a>
                ) : (
                  <p className="muted">Manual entry</p>
                )}
              </div>
            </div>
            <div className="metadata-grid">
              <div>
                <h3 className="card__title">Next Action</h3>
                <p className="muted">{job.next_action || "No next action set"}</p>
              </div>
              <div>
                <h3 className="card__title">Due Date</h3>
                <p className="muted">{job.next_action_due_date ?? "No due date set"}</p>
              </div>
            </div>
            <div>
              <h3 className="card__title">Required Skills</h3>
              <div className="pill-list">
                {job.normalized_requirements.length ? (
                  job.normalized_requirements.map((skill) => (
                    <span className="pill" key={`required-${skill}`}>
                      {skill}
                    </span>
                  ))
                ) : (
                  <span className="muted">No parsed required skills.</span>
                )}
              </div>
            </div>
            <div>
              <h3 className="card__title">Preferred Skills</h3>
              <div className="pill-list">
                {job.normalized_preferred.length ? (
                  job.normalized_preferred.map((skill) => (
                    <span className="pill" key={`preferred-${skill}`}>
                      {skill}
                    </span>
                  ))
                ) : (
                  <span className="muted">No parsed preferred skills.</span>
                )}
              </div>
            </div>
            <div>
              <h3 className="card__title">Notes</h3>
              <p className="muted">{job.notes || "No notes saved yet."}</p>
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Raw Job Text" description="This is the exact text sent to the deterministic parser.">
          <pre className="raw-text">{job.raw_text}</pre>
        </SectionCard>
      </div>

      <AnalysisPanel analysis={analysis} />
      <ApplicationAnswersPanel analysis={analysis} jobId={jobId} />
    </div>
  );
}
