"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { SectionCard } from "@/components/section-card";
import { getJobs } from "@/lib/api";
import type { Job } from "@/lib/types";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  async function loadJobs() {
    try {
      setIsLoading(true);
      setError(null);
      setJobs(await getJobs());
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load jobs.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    let isMounted = true;

    async function initialLoad() {
      try {
        const nextJobs = await getJobs();
        if (!isMounted) {
          return;
        }
        setJobs(nextJobs);
        setError(null);
      } catch (loadError) {
        if (!isMounted) {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Failed to load jobs.");
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
  }, []);

  return (
    <div className="grid">
      <PageHeader
        title="Jobs"
        description="Manage raw internship job entries and jump into detailed analysis for each role."
        actions={
          <Link className="button" href="/jobs/new">
            Add Job
          </Link>
        }
      />

      {error ? (
        <div className="error-banner">
          <div>{error}</div>
          <button className="button button--secondary" onClick={() => void loadJobs()} type="button">
            Retry
          </button>
        </div>
      ) : null}

      <SectionCard
        title="Saved Jobs"
        description="Each entry stores raw job text plus the normalized required and preferred skills from the backend parser."
      >
        {isLoading ? (
          <div className="loading-state">
            <div className="loading-card" />
            <div className="loading-card" />
          </div>
        ) : jobs.length ? (
          <div className="jobs-list">
            {jobs.map((job) => (
              <Link className="card job-card" href={`/jobs/${job.id}`} key={job.id}>
                <div className="job-card__top">
                  <div>
                    <h3 className="job-card__title">{job.title}</h3>
                    <div className="job-card__meta">
                      {job.company_name} • {job.location || "Location not provided"}
                    </div>
                  </div>
                  <span className="pill">Open Detail</span>
                </div>
                <div className="job-card__skills">
                  {job.normalized_requirements.map((skill) => (
                    <span className="pill" key={`${job.id}-${skill}`}>
                      {skill}
                    </span>
                  ))}
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="empty-state-panel">
            <p className="empty-state-title">No jobs saved yet</p>
            <p className="empty-state">Add your first internship posting to start testing the deterministic fit analysis flow.</p>
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
