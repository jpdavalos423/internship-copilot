export type CandidateProfile = {
  id: string;
  resume_text: string;
  normalized_skills: string[];
  created_at: string;
  updated_at: string;
};

export type SaveProfilePayload = {
  resume_text: string;
};

export type Job = {
  id: string;
  company_name: string;
  title: string;
  location: string;
  raw_text: string;
  source_type: "MANUAL" | "GREENHOUSE" | "LEVER" | "ASHBY" | "OTHER";
  source_url: string | null;
  external_id: string | null;
  content_hash: string | null;
  last_seen_at: string | null;
  ingestion_status: "MANUAL" | "INGESTED" | "FAILED";
  is_archived: boolean;
  is_hidden: boolean;
  is_saved: boolean;
  normalized_requirements: string[];
  normalized_preferred: string[];
  created_at: string;
  updated_at: string;
};

export type CreateJobPayload = {
  company_name: string;
  title: string;
  location: string;
  raw_text: string;
};

export type IngestJobUrlPayload = {
  url: string;
};

export type MatchReport = {
  id: string;
  match_report_id: string;
  job_id: string;
  candidate_profile_id: string;
  match_score: number;
  recommendation: string;
  reasoning: string;
  strengths: string[];
  gaps: string[];
  missing_keywords: string[];
  matched_skills_by_category: Record<string, string[]>;
  missing_skills_by_category: Record<string, string[]>;
  score_breakdown: Record<string, string[] | number>;
  created_at: string;
  updated_at: string;
};

export type AnswerType =
  | "WHY_COMPANY"
  | "WHY_ROLE"
  | "GOOD_FIT"
  | "SELF_INTRODUCTION"
  | "MOST_IMPRESSIVE_ACCOMPLISHMENT";

export type GeneratedAnswer = {
  id: string;
  job_id: string;
  candidate_profile_id: string;
  match_report_id: string;
  answer_type: AnswerType;
  content: string;
  evidence_summary: string[];
  generator_version: string;
  created_at: string;
  updated_at: string;
};

export type GeneratedAnswersResponse = {
  job_id: string;
  candidate_profile_id: string | null;
  match_report_id: string;
  answers: GeneratedAnswer[];
};

export type GenerateAnswerPayload = {
  answer_type: AnswerType;
  match_report_id: string;
};
