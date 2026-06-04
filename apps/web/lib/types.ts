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

export type MatchReport = {
  id: string;
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
