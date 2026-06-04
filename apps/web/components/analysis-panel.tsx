import { ScoreBreakdown } from "@/components/score-breakdown";
import { SectionCard } from "@/components/section-card";
import { SkillGroupList } from "@/components/skill-group-list";
import type { MatchReport } from "@/lib/types";

type AnalysisPanelProps = {
  analysis: MatchReport | null;
};

export function AnalysisPanel({ analysis }: AnalysisPanelProps) {
  if (!analysis) {
    return (
      <SectionCard
        title="Analysis"
        description="Run the deterministic analysis to see score, grouped strengths, grouped gaps, and recommendation reasoning."
      >
        <div className="empty-state-panel">
          <p className="empty-state-title">No saved analysis yet</p>
          <p className="empty-state">Use the Run Analysis button to generate the first deterministic fit report for this role.</p>
        </div>
      </SectionCard>
    );
  }

  return (
    <div className="analysis-grid">
      <div className="grid">
        <SectionCard title="Analysis Summary" description="Core decision output from the deterministic scoring engine.">
          <div className="stats-row">
            <div className="stat">
              <p className="stat__label">Match Score</p>
              <p className="stat__value">
                <span className="analysis-score">{analysis.match_score}</span>
              </p>
            </div>
            <div className="stat">
              <p className="stat__label">Recommendation</p>
              <div className={`recommendation-badge recommendation-badge--${analysis.recommendation.toLowerCase()}`}>
                {analysis.recommendation}
              </div>
            </div>
            <div className="stat">
              <p className="stat__label">Keywords Missing</p>
              <p className="stat__value" style={{ fontSize: "1.2rem" }}>
                {analysis.missing_keywords.length}
              </p>
            </div>
          </div>
          <div style={{ marginTop: "1rem" }}>
            <h3 className="card__title">Reasoning</h3>
            <p className="analysis-reasoning">
              {analysis.reasoning}
            </p>
          </div>
        </SectionCard>

        <SectionCard title="Strengths" description="Matched skills surfaced directly from the backend report.">
          {analysis.strengths.length ? (
            <ul className="list">
              {analysis.strengths.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : (
            <p className="empty-state">No strengths were identified.</p>
          )}
        </SectionCard>

        <SectionCard title="Gaps" description="Required-skill gaps currently driving the decision threshold.">
          {analysis.gaps.length ? (
            <ul className="list">
              {analysis.gaps.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : (
            <p className="empty-state">No required-skill gaps were found.</p>
          )}
        </SectionCard>

        <SectionCard title="Missing Keywords" description="Flat keyword view for fast scanning and resume alignment.">
          {analysis.missing_keywords.length ? (
            <div className="pill-list">
              {analysis.missing_keywords.map((item) => (
                <span className="pill" key={item}>
                  {item}
                </span>
              ))}
            </div>
          ) : (
            <p className="empty-state">No missing keywords detected.</p>
          )}
        </SectionCard>
      </div>

      <div className="grid">
        <SectionCard title="Matched Skills by Category" description="Category-grouped view of skills already covered by the resume.">
          <SkillGroupList
            emptyMessage="No matched skills grouped by category yet."
            groups={analysis.matched_skills_by_category}
          />
        </SectionCard>

        <SectionCard title="Missing Skills by Category" description="Category-grouped view of remaining gaps.">
          <SkillGroupList
            emptyMessage="No missing skills grouped by category yet."
            groups={analysis.missing_skills_by_category}
          />
        </SectionCard>

        <SectionCard title="Score Breakdown" description="Underlying deterministic inputs and score components.">
          <ScoreBreakdown breakdown={analysis.score_breakdown} />
        </SectionCard>
      </div>
    </div>
  );
}
