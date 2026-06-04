"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { SectionCard } from "@/components/section-card";
import { getRecruitingPreferences, saveRecruitingPreferences } from "@/lib/api";
import type { RemotePreference, SaveRecruitingPreferencesPayload } from "@/lib/types";

const TARGET_TERM_OPTIONS = ["Fall 2026", "Winter 2027", "Spring 2027", "Summer 2027"];
const ROLE_TYPE_OPTIONS = [
  "Backend",
  "Frontend",
  "Full-stack",
  "Platform",
  "Infrastructure",
  "AI/ML",
  "Data",
  "Mobile",
  "Systems",
  "Developer Tools",
  "Cloud",
];

const REMOTE_OPTIONS: Array<{ value: RemotePreference; label: string }> = [
  { value: "ANY", label: "Any setup" },
  { value: "REMOTE", label: "Remote" },
  { value: "HYBRID", label: "Hybrid" },
  { value: "ONSITE", label: "Onsite" },
];

function parseListInput(value: string) {
  return value
    .split("\n")
    .flatMap((line) => line.split(","))
    .map((item) => item.trim())
    .filter(Boolean);
}

function formatListInput(values: string[]) {
  return values.join("\n");
}

export default function RecruitingPreferencesPage() {
  const [form, setForm] = useState<SaveRecruitingPreferencesPayload | null>(null);
  const [preferredLocationsText, setPreferredLocationsText] = useState("");
  const [preferredIndustriesText, setPreferredIndustriesText] = useState("");
  const [excludedKeywordsText, setExcludedKeywordsText] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    async function loadPreferences() {
      try {
        const preferences = await getRecruitingPreferences();
        if (!isActive) {
          return;
        }
        setForm({
          target_terms: preferences.target_terms,
          role_types: preferences.role_types,
          preferred_locations: preferences.preferred_locations,
          remote_preference: preferences.remote_preference,
          preferred_industries: preferences.preferred_industries,
          excluded_keywords: preferences.excluded_keywords,
          minimum_match_score: preferences.minimum_match_score,
          include_sponsorship_required_roles: preferences.include_sponsorship_required_roles,
          include_clearance_required_roles: preferences.include_clearance_required_roles,
        });
        setPreferredLocationsText(formatListInput(preferences.preferred_locations));
        setPreferredIndustriesText(formatListInput(preferences.preferred_industries));
        setExcludedKeywordsText(formatListInput(preferences.excluded_keywords));
      } catch (loadError) {
        if (!isActive) {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Failed to load recruiting preferences.");
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void loadPreferences();

    return () => {
      isActive = false;
    };
  }, []);

  function updateForm<Key extends keyof SaveRecruitingPreferencesPayload>(
    key: Key,
    value: SaveRecruitingPreferencesPayload[Key],
  ) {
    setForm((current) => (current ? { ...current, [key]: value } : current));
  }

  async function handleSave() {
    if (!form) {
      return;
    }

    try {
      setIsSaving(true);
      setError(null);
      setSuccess(null);
      const payload: SaveRecruitingPreferencesPayload = {
        ...form,
        preferred_locations: parseListInput(preferredLocationsText),
        preferred_industries: parseListInput(preferredIndustriesText),
        excluded_keywords: parseListInput(excludedKeywordsText),
      };
      const saved = await saveRecruitingPreferences(payload);
      setForm({
        target_terms: saved.target_terms,
        role_types: saved.role_types,
        preferred_locations: saved.preferred_locations,
        remote_preference: saved.remote_preference,
        preferred_industries: saved.preferred_industries,
        excluded_keywords: saved.excluded_keywords,
        minimum_match_score: saved.minimum_match_score,
        include_sponsorship_required_roles: saved.include_sponsorship_required_roles,
        include_clearance_required_roles: saved.include_clearance_required_roles,
      });
      setPreferredLocationsText(formatListInput(saved.preferred_locations));
      setPreferredIndustriesText(formatListInput(saved.preferred_industries));
      setExcludedKeywordsText(formatListInput(saved.excluded_keywords));
      setSuccess("Preferences saved. Job relevance has been refreshed across the board.");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Failed to save recruiting preferences.");
    } finally {
      setIsSaving(false);
    }
  }

  const summary = form
    ? `Prioritizing ${form.role_types.length ? form.role_types.join(", ") : "open-ended software"} internships for ${form.target_terms.join(", ")}, with ${form.remote_preference.toLowerCase()} work preference and a minimum match score of ${form.minimum_match_score}.`
    : "";

  return (
    <div className="grid">
      <PageHeader
        title="Recruiting Preferences"
        description="Tune the board so it behaves like JP's internship shortlist instead of a generic tracker."
        actions={
          <Link className="button button--secondary" href="/jobs">
            Return to Jobs
          </Link>
        }
      />

      {error ? <div className="error-banner">{error}</div> : null}
      {success ? <div className="success-banner">{success}</div> : null}

      <div className="split-panel">
        <SectionCard
          title="Preference Settings"
          description="These settings drive relevance classification, filtering, and the default dashboard view."
        >
          {isLoading || !form ? (
            <div className="loading-card" />
          ) : (
            <div className="grid">
              <div className="field">
                <label>Target terms</label>
                <div className="filter-chip-row">
                  {TARGET_TERM_OPTIONS.map((option) => {
                    const isSelected = form.target_terms.includes(option);
                    return (
                      <button
                        className={`filter-chip${isSelected ? " filter-chip--active" : ""}`}
                        key={option}
                        onClick={() =>
                          updateForm(
                            "target_terms",
                            isSelected
                              ? form.target_terms.filter((item) => item !== option)
                              : [...form.target_terms, option],
                          )
                        }
                        type="button"
                      >
                        {option}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="field">
                <label>Role focus</label>
                <div className="filter-chip-row">
                  {ROLE_TYPE_OPTIONS.map((option) => {
                    const isSelected = form.role_types.includes(option);
                    return (
                      <button
                        className={`filter-chip${isSelected ? " filter-chip--active" : ""}`}
                        key={option}
                        onClick={() =>
                          updateForm(
                            "role_types",
                            isSelected
                              ? form.role_types.filter((item) => item !== option)
                              : [...form.role_types, option],
                          )
                        }
                        type="button"
                      >
                        {option}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="form__row">
                <div className="field">
                  <label htmlFor="remotePreference">Remote preference</label>
                  <select
                    id="remotePreference"
                    value={form.remote_preference}
                    onChange={(event) => updateForm("remote_preference", event.target.value as RemotePreference)}
                  >
                    {REMOTE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="field">
                  <label htmlFor="minimumMatchScore">Minimum match score</label>
                  <input
                    id="minimumMatchScore"
                    max={100}
                    min={0}
                    type="number"
                    value={form.minimum_match_score}
                    onChange={(event) => updateForm("minimum_match_score", Number(event.target.value))}
                  />
                </div>
              </div>

              <div className="field">
                <label htmlFor="preferredLocations">Preferred locations</label>
                <textarea
                  id="preferredLocations"
                  value={preferredLocationsText}
                  onChange={(event) => setPreferredLocationsText(event.target.value)}
                />
                <p className="helper-text">Enter one location per line or use commas.</p>
              </div>

              <div className="field">
                <label htmlFor="preferredIndustries">Preferred industries</label>
                <textarea
                  id="preferredIndustries"
                  value={preferredIndustriesText}
                  onChange={(event) => setPreferredIndustriesText(event.target.value)}
                />
              </div>

              <div className="field">
                <label htmlFor="excludedKeywords">Excluded keywords</label>
                <textarea
                  id="excludedKeywords"
                  value={excludedKeywordsText}
                  onChange={(event) => setExcludedKeywordsText(event.target.value)}
                />
              </div>

              <label className="checkbox-field">
                <input
                  checked={form.include_sponsorship_required_roles}
                  type="checkbox"
                  onChange={(event) =>
                    updateForm("include_sponsorship_required_roles", event.target.checked)
                  }
                />
                <span>Include roles that appear to require sponsorship</span>
              </label>

              <label className="checkbox-field">
                <input
                  checked={form.include_clearance_required_roles}
                  type="checkbox"
                  onChange={(event) =>
                    updateForm("include_clearance_required_roles", event.target.checked)
                  }
                />
                <span>Include roles that appear to require clearance</span>
              </label>

              <div>
                <button className="button" disabled={isSaving} onClick={() => void handleSave()} type="button">
                  {isSaving ? "Saving..." : "Save Preferences"}
                </button>
              </div>
            </div>
          )}
        </SectionCard>

        <SectionCard
          title="Board Behavior"
          description="This summary gives you a quick read on how the board will prioritize jobs."
        >
          {isLoading || !form ? <div className="loading-card" /> : <p className="muted">{summary}</p>}
        </SectionCard>
      </div>
    </div>
  );
}
