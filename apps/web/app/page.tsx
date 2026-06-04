import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { SectionCard } from "@/components/section-card";

export default function HomePage() {
  return (
    <div className="grid">
      <PageHeader
        title="Phase 0 Dashboard"
        description="Use the profile and jobs flows to paste a resume, add a role, and run deterministic fit analysis."
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
          title="2. Add Job"
          description="Create a job from company, role title, location, and the raw internship description."
        />
        <SectionCard
          title="3. Run Analysis"
          description="Open the job detail page to generate match score, reasoning, grouped strengths, and missing skills."
        />
      </div>
    </div>
  );
}
