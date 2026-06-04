import { apiBaseUrl } from "@/lib/config";
import type {
  CandidateProfile,
  CreateJobPayload,
  GenerateAnswerPayload,
  GeneratedAnswer,
  GeneratedAnswersResponse,
  IngestJobUrlPayload,
  Job,
  MatchReport,
  SaveProfilePayload,
} from "@/lib/types";

type ApiErrorPayload = {
  error?: {
    code?: string;
    message?: string;
  };
};

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

async function executeRequest(path: string, init?: RequestInit): Promise<Response> {
  let response: Response;
  const headers = new Headers(init?.headers ?? {});

  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...init,
      headers,
      cache: "no-store",
    });
  } catch {
    throw new Error("Unable to reach the API. Make sure the Django server is running and the API base URL is correct.");
  }

  return response;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await executeRequest(path, init);

  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}.`;
    let errorCode: string | undefined;

    try {
      const payload = (await response.json()) as ApiErrorPayload;
      errorCode = payload.error?.code;
      if (payload.error?.message) {
        errorMessage = payload.error.message;
      }
    } catch {}

    throw new ApiError(errorMessage, response.status, errorCode);
  }

  return (await response.json()) as T;
}

async function requestWithMeta<T>(path: string, init?: RequestInit): Promise<{ data: T; status: number }> {
  const response = await executeRequest(path, init);

  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}.`;
    let errorCode: string | undefined;

    try {
      const payload = (await response.json()) as ApiErrorPayload;
      errorCode = payload.error?.code;
      if (payload.error?.message) {
        errorMessage = payload.error.message;
      }
    } catch {}

    throw new ApiError(errorMessage, response.status, errorCode);
  }

  return {
    data: (await response.json()) as T,
    status: response.status,
  };
}

export function getProfile() {
  return request<CandidateProfile>("/profile");
}

export async function getOptionalProfile() {
  try {
    return await getProfile();
  } catch (error) {
    if (error instanceof ApiError && error.status === 404 && error.code === "CANDIDATE_PROFILE_NOT_FOUND") {
      return null;
    }
    throw error;
  }
}

export function saveProfile(payload: SaveProfilePayload) {
  return request<CandidateProfile>("/profile", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getJobs() {
  return request<Job[]>("/jobs");
}

export function createJob(payload: CreateJobPayload) {
  return request<Job>("/jobs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function ingestJobUrl(payload: IngestJobUrlPayload) {
  const response = await requestWithMeta<Job>("/jobs/ingest-url", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  return {
    job: response.data,
    created: response.status === 201,
  };
}

export function getJob(jobId: string) {
  return request<Job>(`/jobs/${jobId}`);
}

export function analyzeJob(jobId: string) {
  return request<MatchReport>(`/jobs/${jobId}/analyze`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function getJobAnalysis(jobId: string) {
  return request<MatchReport>(`/jobs/${jobId}/analysis`);
}

export async function getLatestJobAnalysis(jobId: string) {
  try {
    return await getJobAnalysis(jobId);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404 && error.code === "MATCH_REPORT_NOT_FOUND") {
      return null;
    }
    throw error;
  }
}

export function getJobAnalysisById(jobId: string, matchReportId: string) {
  return request<MatchReport>(`/jobs/${jobId}/analysis/${matchReportId}`);
}

export function getJobAnswers(jobId: string, matchReportId?: string) {
  const search = matchReportId ? `?match_report_id=${matchReportId}` : "";
  return request<GeneratedAnswersResponse>(`/jobs/${jobId}/answers${search}`);
}

export function generateJobAnswer(jobId: string, payload: GenerateAnswerPayload) {
  return request<GeneratedAnswer>(`/jobs/${jobId}/answers/generate`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
