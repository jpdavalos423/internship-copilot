"use client";

import { useEffect, useRef, useState } from "react";
import { SectionCard } from "@/components/section-card";
import { generateJobAnswer, getJobAnswers } from "@/lib/api";
import type { AnswerType, GeneratedAnswer, MatchReport } from "@/lib/types";

const ANSWER_CONFIG: Array<{ type: AnswerType; title: string; description: string }> = [
  {
    type: "WHY_COMPANY",
    title: "Why This Company",
    description: "Grounded in the saved posting and the overlap between the role and your saved profile.",
  },
  {
    type: "WHY_ROLE",
    title: "Why This Role",
    description: "Focused on responsibilities and technologies already reflected in your saved background.",
  },
  {
    type: "GOOD_FIT",
    title: "Why You're a Good Fit",
    description: "Based on the saved match report and its strongest skill overlap.",
  },
  {
    type: "SELF_INTRODUCTION",
    title: "Self Introduction",
    description: "A concise intro generated from the saved resume, role, and analysis context.",
  },
  {
    type: "MOST_IMPRESSIVE_ACCOMPLISHMENT",
    title: "Most Impressive Accomplishment",
    description: "Selects a resume-supported accomplishment without adding unsupported scope or metrics.",
  },
];

type ApplicationAnswersPanelProps = {
  jobId: string;
  analysis: MatchReport | null;
};

export function ApplicationAnswersPanel({ jobId, analysis }: ApplicationAnswersPanelProps) {
  const [answersByType, setAnswersByType] = useState<Partial<Record<AnswerType, GeneratedAnswer>>>({});
  const [isLoadingAnswers, setIsLoadingAnswers] = useState(false);
  const [answersError, setAnswersError] = useState<string | null>(null);
  const [generatingType, setGeneratingType] = useState<AnswerType | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const loadedMatchReportIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!analysis) {
      loadedMatchReportIdRef.current = null;
      return;
    }

    if (loadedMatchReportIdRef.current === analysis.match_report_id) {
      return;
    }
    loadedMatchReportIdRef.current = analysis.match_report_id;
    const activeAnalysis = analysis;

    async function loadAnswers() {
      try {
        setIsLoadingAnswers(true);
        setAnswersError(null);
        setSuccessMessage(null);
        const response = await getJobAnswers(jobId, activeAnalysis.match_report_id);
        setAnswersByType(
          Object.fromEntries(response.answers.map((answer) => [answer.answer_type, answer])),
        );
      } catch (loadError) {
        setAnswersError(loadError instanceof Error ? loadError.message : "Failed to load generated answers.");
      } finally {
        setIsLoadingAnswers(false);
      }
    }

    void loadAnswers();
  }, [analysis, jobId]);

  async function handleGenerate(answerType: AnswerType) {
    if (!analysis) {
      return;
    }

    try {
      setGeneratingType(answerType);
      setAnswersError(null);
      setSuccessMessage(null);
      const answer = await generateJobAnswer(jobId, {
        answer_type: answerType,
        match_report_id: analysis.match_report_id,
      });
      setAnswersByType((current) => ({
        ...current,
        [answerType]: answer,
      }));
      const label = ANSWER_CONFIG.find((item) => item.type === answerType)?.title ?? "Answer";
      setSuccessMessage(`${label} generated successfully.`);
    } catch (generateError) {
      setAnswersError(generateError instanceof Error ? generateError.message : "Failed to generate answer.");
    } finally {
      setGeneratingType(null);
    }
  }

  return (
    <SectionCard
      title="Application Answers"
      description="Generate saved, resume-grounded answers for common application prompts. Nothing is generated until you click a button."
    >
      {!analysis ? (
        <div className="empty-state-panel">
          <p className="empty-state-title">Run analysis first</p>
          <p className="empty-state">Save an analysis for this job before generating application answers.</p>
        </div>
      ) : (
        <div className="grid">
          {answersError ? <div className="error-banner">{answersError}</div> : null}
          {successMessage ? <div className="success-banner">{successMessage}</div> : null}
          {isLoadingAnswers ? <div className="loading-card" /> : null}

          <div className="answers-grid">
            {ANSWER_CONFIG.map((config) => {
              const answer = answersByType[config.type];
              const isGenerating = generatingType === config.type;

              return (
                <section className="answer-card" key={config.type}>
                  <div className="answer-card__header">
                    <div>
                      <h3 className="card__title">{config.title}</h3>
                      <p className="card__description">{config.description}</p>
                    </div>
                    <button
                      className="button button--secondary"
                      disabled={isGenerating}
                      onClick={() => void handleGenerate(config.type)}
                      type="button"
                    >
                      {isGenerating ? "Generating..." : answer ? "Regenerate" : "Generate"}
                    </button>
                  </div>

                  {answer ? (
                    <div className="answer-card__content">
                      <p className="answer-card__body">{answer.content}</p>
                      <div className="answer-card__footer">
                        <p className="answer-card__meta">
                          Saved for report {answer.match_report_id.slice(0, 8)} using {answer.generator_version}.
                        </p>
                        <div className="pill-list">
                          {answer.evidence_summary.map((item) => (
                            <span className="pill" key={`${answer.id}-${item}`}>
                              {item}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="empty-state-panel empty-state-panel--compact">
                      <p className="empty-state-title">Not generated yet</p>
                      <p className="empty-state">This answer will only be created when you request it.</p>
                    </div>
                  )}
                </section>
              );
            })}
          </div>
        </div>
      )}
    </SectionCard>
  );
}
