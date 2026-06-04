"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { AnalysisPanel } from "@/components/analysis-panel";
import { PageHeader } from "@/components/page-header";
import { SectionCard } from "@/components/section-card";
import { analyzeJob, getJob, getJobAnalysis } from "@/lib/api";
import type { Job, MatchReport } from "@/lib/types";

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const jobId = params.id;
  const createdMessage =
    searchParams.get("created") === "1"
      ? "Job created successfully. Review the parsed skills below, then run analysis."
      : null;

  const [job, setJob] = useState<Job | null>(null);
  const [analysis, setAnalysis] = useState<MatchReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  async function loadJobAndAnalysis() {
    try {
      setIsLoading(true);
      setError(null);
      setAnalysisError(null);
      const loadedJob = await getJob(jobId);
      setJob(loadedJob);

      try {
        const loadedAnalysis = await getJobAnalysis(jobId);
        setAnalysis(loadedAnalysis);
      } catch (analysisLoadError) {
        const message =
          analysisLoadError instanceof Error ? analysisLoadError.message : "No saved analysis yet.";
        if (message.toLowerCase().includes("not found")) {
          setAnalysis(null);
        } else {
          setAnalysisError(message);
        }
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load job.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    let isMounted = true;

    async function initialLoad() {
      try {
        const loadedJob = await getJob(jobId);
        if (!isMounted) {
          return;
        }
        setJob(loadedJob);
        setError(null);

        try {
          const loadedAnalysis = await getJobAnalysis(jobId);
          if (isMounted) {
            setAnalysis(loadedAnalysis);
            setAnalysisError(null);
          }
        } catch (analysisLoadError) {
          if (!isMounted) {
            return;
          }
          const message =
            analysisLoadError instanceof Error ? analysisLoadError.message : "No saved analysis yet.";
          if (message.toLowerCase().includes("not found")) {
            setAnalysis(null);
          } else {
            setAnalysisError(message);
          }
        }
      } catch (loadError) {
        if (!isMounted) {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Failed to load job.");
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void initialLoad();

    return () => {
      isMounted = false;
    };
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
          <button className="button" disabled={isAnalyzing} onClick={handleAnalyze} type="button">
            {isAnalyzing ? "Running Analysis..." : "Run Analysis"}
          </button>
        }
      />

      {createdMessage || success ? <div className="success-banner">{createdMessage ?? success}</div> : null}
      {analysisError ? <div className="error-banner">{analysisError}</div> : null}
      {!analysis && !analysisError ? (
        <div className="info-banner">
          No analysis has been run yet for this job. Use the Run Analysis button to generate the first report.
        </div>
      ) : null}

      <div className="split-panel">
        <SectionCard title="Job Metadata" description="Normalized skills are parsed and persisted by the Django backend.">
          <div className="grid">
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
          </div>
        </SectionCard>

        <SectionCard title="Raw Job Text" description="This is the exact text sent to the deterministic parser.">
          <pre className="raw-text">{job.raw_text}</pre>
        </SectionCard>
      </div>

      <AnalysisPanel analysis={analysis} />
    </div>
  );
}
