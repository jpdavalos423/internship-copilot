"use client";

import { useEffect, useRef, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { ProfileForm } from "@/components/profile-form";
import { SectionCard } from "@/components/section-card";
import { getOptionalProfile, saveProfile } from "@/lib/api";
import type { CandidateProfile } from "@/lib/types";

export default function ProfilePage() {
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [resumeText, setResumeText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [hasProfile, setHasProfile] = useState(false);
  const hasLoadedRef = useRef(false);

  async function loadProfile() {
    try {
      setIsLoading(true);
      setError(null);
      const existingProfile = await getOptionalProfile();
      if (existingProfile) {
        setProfile(existingProfile);
        setResumeText(existingProfile.resume_text);
        setHasProfile(true);
      } else {
        setProfile(null);
        setResumeText("");
        setHasProfile(false);
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load profile.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (hasLoadedRef.current) {
      return;
    }
    hasLoadedRef.current = true;

    void loadProfile();
  }, []);

  async function handleSave() {
    if (!resumeText.trim()) {
      setValidationError("Resume text is required before you can save the profile.");
      return;
    }

    setIsSaving(true);
    setError(null);
    setSuccess(null);
    setValidationError(null);

    try {
      const savedProfile = await saveProfile({ resume_text: resumeText.trim() });
      setProfile(savedProfile);
      setResumeText(savedProfile.resume_text);
      setHasProfile(true);
      setSuccess("Profile saved successfully. Normalized skills were refreshed from your latest resume text.");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Failed to save profile.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="grid">
      <PageHeader
        title="Candidate Profile"
        description="Paste your current resume text. The backend will normalize skills deterministically and reuse them for job analysis."
      />

      {error ? (
        <div className="error-banner">
          <div>{error}</div>
          <button className="button button--secondary" onClick={() => void loadProfile()} type="button">
            Retry
          </button>
        </div>
      ) : null}
      {success ? <div className="success-banner">{success}</div> : null}
      {!isLoading && !hasProfile && !error ? (
        <div className="info-banner">
          No profile is saved yet. Paste your resume text below to create the candidate profile used for all job analysis.
        </div>
      ) : null}

      <div className="grid grid--two">
        <SectionCard title="Resume Text" description="Keep this aligned with the resume you are actively using.">
          <ProfileForm
            resumeText={resumeText}
            isLoading={isLoading}
            isSaving={isSaving}
            validationError={validationError}
            onResumeTextChange={setResumeText}
            onSave={handleSave}
          />
        </SectionCard>

        <SectionCard
          title="Normalized Skills"
          description="These are the taxonomy-matched skills currently available to the scoring engine."
        >
          {profile?.normalized_skills.length ? (
            <div className="pill-list">
              {profile.normalized_skills.map((skill) => (
                <span className="pill" key={skill}>
                  {skill}
                </span>
              ))}
            </div>
          ) : (
            <div className="empty-state-panel">
              <p className="empty-state-title">{isLoading ? "Loading profile..." : "No normalized skills yet"}</p>
              <p className="empty-state">
                {isLoading
                  ? "Fetching the current candidate profile."
                  : "Save your resume text to generate the skill snapshot the scoring engine will use."}
              </p>
            </div>
          )}
        </SectionCard>
      </div>
    </div>
  );
}
