import type {
  PreArrivalSubmissionRequest,
  PreArrivalSubmissionResult,
} from "@epicenter/shared/contracts";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
type AccessTokenProvider = () => Promise<string | null>;

let accessTokenProvider: AccessTokenProvider | null = null;

export function setAccessTokenProvider(provider: AccessTokenProvider | null) {
  accessTokenProvider = provider;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const accessToken = await accessTokenProvider?.();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? "The clinic service could not process this request.");
  }
  return response.json() as Promise<T>;
}

export function activatePatientAccount(): Promise<{ patient_id: number; source_record_key: string }> {
  return request("/patient/account/activate", { method: "POST" });
}

export async function submitPreArrival(
  payload: PreArrivalSubmissionRequest,
): Promise<PreArrivalSubmissionResult> {
  return request("/patient/pre-arrival/submit", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
