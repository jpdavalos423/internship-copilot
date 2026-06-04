export type CandidateProfile = {
  id: string;
  resume_text: string;
  normalized_skills: string[];
  created_at: string;
  updated_at: string;
};

export type RemotePreference = "REMOTE" | "HYBRID" | "ONSITE" | "ANY";
export type PositionTypePreference = "INTERN" | "FULL_TIME" | "PART_TIME";
export type JobPositionType = PositionTypePreference | "UNKNOWN";

export type RecruitingPreferences = {
  id: string;
  target_terms: string[];
  role_types: string[];
  position_types: PositionTypePreference[];
  preferred_locations: string[];
  remote_preference: RemotePreference;
  preferred_industries: string[];
  excluded_keywords: string[];
  minimum_match_score: number;
  include_sponsorship_required_roles: boolean;
  include_clearance_required_roles: boolean;
  created_at: string;
  updated_at: string;
};

export type SaveRecruitingPreferencesPayload = Omit<RecruitingPreferences, "id" | "created_at" | "updated_at">;

export type JobRelevance = "HIGHLY_RELEVANT" | "RELEVANT" | "REVIEW" | "NOT_RELEVANT";
export type JobSourceType = "GREENHOUSE" | "LEVER" | "ASHBY";

export type DiscoveryScanSummary = {
  discovered_count: number;
  created_count: number;
  duplicate_count: number;
  failed_count: number;
  skipped_count: number;
  errors: string[];
};

export type JobSource = {
  id: string;
  name: string;
  source_type: JobSourceType;
  base_url: string;
  company_name: string;
  is_active: boolean;
  last_scanned_at: string | null;
  last_success_at: string | null;
  last_error: string;
  scan_interval_hours: number;
  last_scan_summary: DiscoveryScanSummary;
  created_at: string;
  updated_at: string;
};

export type CreateJobSourcePayload = Pick<
  JobSource,
  "name" | "source_type" | "base_url" | "company_name" | "is_active" | "scan_interval_hours"
>;

export type UpdateJobSourcePayload = Partial<CreateJobSourcePayload>;

export type ScanSourceResponse = {
  source: JobSource;
  summary: DiscoveryScanSummary;
};

export type ScanAllSourcesResponse = {
  summary: DiscoveryScanSummary;
  results: ScanSourceResponse[];
};

export type SaveProfilePayload = {
  resume_text: string;
};

export type Job = {
  id: string;
  company_name: string;
  title: string;
  location: string;
  position_type: JobPositionType;
  raw_text: string;
  source_type: "MANUAL" | "GREENHOUSE" | "LEVER" | "ASHBY" | "OTHER";
  source_url: string | null;
  external_id: string | null;
  content_hash: string | null;
  last_seen_at: string | null;
  ingestion_status: "MANUAL" | "INGESTED" | "FAILED";
  workflow_status:
    | "DISCOVERED"
    | "SAVED"
    | "APPLIED"
    | "OA"
    | "INTERVIEW"
    | "FINAL_ROUND"
    | "OFFER"
    | "REJECTED"
    | "WITHDRAWN";
  applied_date: string | null;
  notes: string;
  next_action: string;
  next_action_due_date: string | null;
  is_archived: boolean;
  is_hidden: boolean;
  is_saved: boolean;
  normalized_requirements: string[];
  normalized_preferred: string[];
  relevance: JobRelevance;
  relevance_reasons: string[];
  relevance_flags: string[];
  relevance_last_evaluated_at: string | null;
  relevance_score: number | null;
  created_at: string;
  updated_at: string;
  latest_match_score: number | null;
  latest_recommendation: string | null;
  latest_match_report_id: string | null;
  latest_analysis_created_at: string | null;
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

export type JobWorkflowStatus = Job["workflow_status"];

export type JobSort =
  | "match_score_desc"
  | "match_score_asc"
  | "newest_first"
  | "updated_at_desc"
  | "created_at_desc"
  | "company_asc";

export type JobsQuery = {
  view?: "relevant" | "all";
  relevance?: JobRelevance[];
  status?: JobWorkflowStatus[];
  position_type?: JobPositionType[];
  hide_not_relevant?: boolean;
  recently_added?: boolean;
  include_archived?: boolean;
  sort?: JobSort;
};

export type UpdateJobPayload = Partial<
  Pick<Job, "workflow_status" | "applied_date" | "notes" | "next_action" | "next_action_due_date" | "is_archived">
>;

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
