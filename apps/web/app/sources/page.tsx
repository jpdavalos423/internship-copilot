"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { SectionCard } from "@/components/section-card";
import { createJobSource, getJobSources, scanAllJobSources, scanJobSource, updateJobSource } from "@/lib/api";
import type {
  CreateJobSourcePayload,
  DiscoveryScanSummary,
  JobSource,
  JobSourceType,
  ScanAllSourcesResponse,
} from "@/lib/types";

const SOURCE_OPTIONS: Array<{ value: JobSourceType; label: string }> = [
  { value: "GREENHOUSE", label: "Greenhouse" },
  { value: "LEVER", label: "Lever" },
  { value: "ASHBY", label: "Ashby" },
];

function formatDateTime(value: string | null) {
  if (!value) {
    return "Not yet";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

function emptySummary(): DiscoveryScanSummary {
  return {
    discovered_count: 0,
    created_count: 0,
    duplicate_count: 0,
    failed_count: 0,
    skipped_count: 0,
    errors: [],
  };
}

export default function SourcesPage() {
  const [sources, setSources] = useState<JobSource[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [isScanningAll, setIsScanningAll] = useState(false);
  const [activeSourceId, setActiveSourceId] = useState<string | null>(null);
  const [lastSummary, setLastSummary] = useState<DiscoveryScanSummary | null>(null);
  const [form, setForm] = useState<CreateJobSourcePayload>({
    name: "",
    company_name: "",
    source_type: "GREENHOUSE",
    base_url: "",
    is_active: true,
    scan_interval_hours: 24,
  });
  const [validationErrors, setValidationErrors] = useState<
    Partial<Record<"name" | "company_name" | "base_url" | "scan_interval_hours", string>>
  >({});

  useEffect(() => {
    let isActive = true;

    async function loadSources() {
      try {
        const data = await getJobSources();
        if (!isActive) {
          return;
        }
        setSources(data);
        setError(null);
      } catch (loadError) {
        if (!isActive) {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Failed to load job sources.");
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void loadSources();

    return () => {
      isActive = false;
    };
  }, []);

  function validateForm() {
    const nextErrors: Partial<Record<"name" | "company_name" | "base_url" | "scan_interval_hours", string>> = {};

    if (!form.name.trim()) {
      nextErrors.name = "Source name is required.";
    }
    if (!form.company_name.trim()) {
      nextErrors.company_name = "Company name is required.";
    }
    if (!form.base_url.trim()) {
      nextErrors.base_url = "Board URL is required.";
    }
    if (!Number.isFinite(form.scan_interval_hours) || form.scan_interval_hours < 1) {
      nextErrors.scan_interval_hours = "Scan interval must be at least 1 hour.";
    }

    setValidationErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function handleCreateSource() {
    if (!validateForm()) {
      return;
    }

    try {
      setIsCreating(true);
      setError(null);
      setSuccess(null);
      const created = await createJobSource({
        ...form,
        name: form.name.trim(),
        company_name: form.company_name.trim(),
        base_url: form.base_url.trim(),
      });
      setSources((current) => [...current, created].sort((left, right) => left.company_name.localeCompare(right.company_name)));
      setForm({
        name: "",
        company_name: "",
        source_type: "GREENHOUSE",
        base_url: "",
        is_active: true,
        scan_interval_hours: 24,
      });
      setValidationErrors({});
      setSuccess("Source added successfully.");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Failed to add source.");
    } finally {
      setIsCreating(false);
    }
  }

  async function handleToggleSource(source: JobSource) {
    try {
      setActiveSourceId(source.id);
      setError(null);
      setSuccess(null);
      const updated = await updateJobSource(source.id, { is_active: !source.is_active });
      setSources((current) => current.map((item) => (item.id === source.id ? updated : item)));
      setSuccess(updated.is_active ? "Source enabled." : "Source disabled.");
    } catch (toggleError) {
      setError(toggleError instanceof Error ? toggleError.message : "Failed to update source.");
    } finally {
      setActiveSourceId(null);
    }
  }

  async function handleScanSource(source: JobSource) {
    try {
      setActiveSourceId(source.id);
      setError(null);
      setSuccess(null);
      const result = await scanJobSource(source.id);
      setSources((current) => current.map((item) => (item.id === source.id ? result.source : item)));
      setLastSummary(result.summary);
      setSuccess(`Scan completed for ${result.source.company_name}.`);
    } catch (scanError) {
      setError(scanError instanceof Error ? scanError.message : "Failed to scan source.");
    } finally {
      setActiveSourceId(null);
    }
  }

  async function handleScanAll() {
    try {
      setIsScanningAll(true);
      setError(null);
      setSuccess(null);
      const result: ScanAllSourcesResponse = await scanAllJobSources();
      setSources((current) => {
        const updates = new Map(result.results.map((item) => [item.source.id, item.source]));
        return current.map((item) => updates.get(item.id) ?? item);
      });
      setLastSummary(result.summary);
      setSuccess("Scan all completed.");
    } catch (scanError) {
      setError(scanError instanceof Error ? scanError.message : "Failed to scan all sources.");
    } finally {
      setIsScanningAll(false);
    }
  }

  const totals = sources.reduce(
    (accumulator, source) => {
      const summary = source.last_scan_summary ?? emptySummary();
      accumulator.sources += 1;
      accumulator.active += source.is_active ? 1 : 0;
      accumulator.created += summary.created_count;
      accumulator.discovered += summary.discovered_count;
      return accumulator;
    },
    { sources: 0, active: 0, created: 0, discovered: 0 },
  );

  return (
    <div className="grid">
      <PageHeader
        title="Discovery Sources"
        description="Manage the provider-hosted internship boards that feed your personalized job board."
        actions={
          <>
            <Link className="button button--secondary" href="/jobs?view=all&recently_added=true">
              Recent Discoveries
            </Link>
            <button className="button" disabled={isScanningAll || sources.length === 0} onClick={handleScanAll} type="button">
              {isScanningAll ? "Scanning..." : "Scan All"}
            </button>
          </>
        }
      />

      {error ? <div className="error-banner">{error}</div> : null}
      {success ? <div className="success-banner">{success}</div> : null}
      {lastSummary ? (
        <div className="info-banner">
          <span>
            Last scan summary: {lastSummary.created_count} created, {lastSummary.duplicate_count} duplicates,{" "}
            {lastSummary.failed_count} failed, {lastSummary.skipped_count} skipped.
          </span>
          <Link className="link" href="/jobs?view=all&recently_added=true">
            View discovered jobs
          </Link>
        </div>
      ) : null}

      <div className="stats-row">
        <div className="stat">
          <p className="stat__label">Tracked sources</p>
          <p className="stat__value">{totals.sources}</p>
        </div>
        <div className="stat">
          <p className="stat__label">Active</p>
          <p className="stat__value">{totals.active}</p>
        </div>
        <div className="stat">
          <p className="stat__label">Last discovered</p>
          <p className="stat__value">{totals.discovered}</p>
        </div>
      </div>

      <SectionCard
        title="Add Source"
        description="Add a provider-hosted Greenhouse, Lever, or Ashby board. Phase 5 intentionally avoids custom career page scraping."
      >
        <div className="form">
          <div className="form__row">
            <div className="field">
              <label htmlFor="sourceName">Source name</label>
              <input
                id="sourceName"
                onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                placeholder="Orbit Labs Internships"
                value={form.name}
              />
              {validationErrors.name ? <p className="field-error">{validationErrors.name}</p> : null}
            </div>

            <div className="field">
              <label htmlFor="companyName">Company name</label>
              <input
                id="companyName"
                onChange={(event) => setForm((current) => ({ ...current, company_name: event.target.value }))}
                placeholder="Orbit Labs"
                value={form.company_name}
              />
              {validationErrors.company_name ? <p className="field-error">{validationErrors.company_name}</p> : null}
            </div>
          </div>

          <div className="form__row">
            <div className="field">
              <label htmlFor="sourceType">Source type</label>
              <select
                id="sourceType"
                onChange={(event) =>
                  setForm((current) => ({ ...current, source_type: event.target.value as JobSourceType }))
                }
                value={form.source_type}
              >
                {SOURCE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="field">
              <label htmlFor="scanInterval">Scan interval (hours)</label>
              <input
                id="scanInterval"
                min={1}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    scan_interval_hours: Number(event.target.value || "0"),
                  }))
                }
                type="number"
                value={form.scan_interval_hours}
              />
              {validationErrors.scan_interval_hours ? (
                <p className="field-error">{validationErrors.scan_interval_hours}</p>
              ) : null}
            </div>
          </div>

          <div className="field">
            <label htmlFor="baseUrl">Board URL</label>
            <input
              id="baseUrl"
              onChange={(event) => setForm((current) => ({ ...current, base_url: event.target.value }))}
              placeholder="https://boards.greenhouse.io/company"
              value={form.base_url}
            />
            <p className="helper-text">Supported patterns: `boards.greenhouse.io`, `jobs.lever.co`, `jobs.ashbyhq.com`.</p>
            {validationErrors.base_url ? <p className="field-error">{validationErrors.base_url}</p> : null}
          </div>

          <label className="checkbox-field" htmlFor="sourceActive">
            <input
              checked={form.is_active}
              id="sourceActive"
              onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.checked }))}
              type="checkbox"
            />
            Enable scans immediately
          </label>

          <div>
            <button className="button" disabled={isCreating} onClick={handleCreateSource} type="button">
              {isCreating ? "Adding..." : "Add Source"}
            </button>
          </div>
        </div>
      </SectionCard>

      <SectionCard
        title="Tracked Sources"
        description="Scan individual sources, disable boards temporarily, and review the latest discovery outcomes."
      >
        {isLoading ? (
          <div className="loading-state">
            <div className="loading-card" />
            <div className="loading-card" />
          </div>
        ) : sources.length === 0 ? (
          <div className="empty-state-panel">
            <p className="empty-state-title">No job sources yet.</p>
            <p className="empty-state">Add your first provider-hosted board above to start automated discovery.</p>
          </div>
        ) : (
          <div className="dashboard-job-list">
            {sources.map((source) => (
              <article className="dashboard-job-card" key={source.id}>
                <div className="dashboard-job-card__header">
                  <div>
                    <div className="dashboard-job-card__pills">
                      <span className="status-pill">{source.source_type}</span>
                      <span className={`status-pill${source.is_active ? " status-pill--success" : " status-pill--danger"}`}>
                        {source.is_active ? "Active" : "Disabled"}
                      </span>
                    </div>
                    <h3 className="job-card__title">{source.name}</h3>
                    <p className="job-card__meta">
                      {source.company_name} · every {source.scan_interval_hours}h
                    </p>
                    <p className="muted">
                      <a className="link link--inline" href={source.base_url} rel="noreferrer" target="_blank">
                        {source.base_url}
                      </a>
                    </p>
                  </div>

                  <div className="dashboard-job-card__actions">
                    <button
                      className="button button--secondary"
                      disabled={activeSourceId === source.id}
                      onClick={() => handleToggleSource(source)}
                      type="button"
                    >
                      {activeSourceId === source.id ? "Saving..." : source.is_active ? "Disable" : "Enable"}
                    </button>
                    <button
                      className="button"
                      disabled={activeSourceId === source.id}
                      onClick={() => handleScanSource(source)}
                      type="button"
                    >
                      {activeSourceId === source.id ? "Scanning..." : "Scan Now"}
                    </button>
                  </div>
                </div>

                <div className="dashboard-job-card__details">
                  <div>
                    <strong>Last scanned</strong>
                    <p>{formatDateTime(source.last_scanned_at)}</p>
                  </div>
                  <div>
                    <strong>Last success</strong>
                    <p>{formatDateTime(source.last_success_at)}</p>
                  </div>
                  <div>
                    <strong>Found / Created</strong>
                    <p>
                      {source.last_scan_summary.discovered_count} / {source.last_scan_summary.created_count}
                    </p>
                  </div>
                  <div>
                    <strong>Duplicates / Failed</strong>
                    <p>
                      {source.last_scan_summary.duplicate_count} / {source.last_scan_summary.failed_count}
                    </p>
                  </div>
                </div>

                {source.last_error ? (
                  <div className="error-banner">{source.last_error}</div>
                ) : source.last_scan_summary.errors.length > 0 ? (
                  <div className="info-banner">
                    <span>{source.last_scan_summary.errors[0]}</span>
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}
