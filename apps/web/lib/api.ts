import { apiBaseUrl } from "@/lib/config";
import type {
  CandidateProfile,
  CreateJobPayload,
  Job,
  MatchReport,
  SaveProfilePayload,
} from "@/lib/types";

type ApiErrorPayload = {
  error?: {
    message?: string;
  };
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
      cache: "no-store",
    });
  } catch {
    throw new Error("Unable to reach the API. Make sure the Django server is running and the API base URL is correct.");
  }

  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}.`;

    try {
      const payload = (await response.json()) as ApiErrorPayload;
      if (payload.error?.message) {
        errorMessage = payload.error.message;
      }
    } catch {}

    throw new Error(errorMessage);
  }

  return (await response.json()) as T;
}

export function getProfile() {
  return request<CandidateProfile>("/profile");
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
