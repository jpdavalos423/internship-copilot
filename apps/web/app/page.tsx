import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { SectionCard } from "@/components/section-card";

export default function HomePage() {
  return (
    <div className="grid">
      <PageHeader
        title="Internship Dashboard"
        description="Save your profile, build a personalized internship board, and use deterministic analysis to prioritize where to apply."
        actions={
          <>
            <Link className="button" href="/profile">
              Open Profile
            </Link>
            <Link className="button button--secondary" href="/jobs">
              View Jobs
            </Link>
          </>
        }
      />

      <div className="grid grid--three">
        <SectionCard
          title="1. Save Resume"
          description="Paste resume text into the profile page and persist the normalized skill snapshot."
        />
        <SectionCard
          title="2. Build Your Board"
          description="Add jobs manually or by URL, then use relevance preferences to surface the roles that fit JP's search."
        />
        <SectionCard
          title="3. Run Analysis"
          description="Open a job detail page to generate match score, reasoning, grouped strengths, and missing skills."
        />
      </div>
    </div>
  );
}
