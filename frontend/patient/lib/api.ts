import type {
  PreArrivalSubmissionRequest,
  PreArrivalSubmissionResult,
} from "@epicenter/shared/contracts";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function submitPreArrival(
  payload: PreArrivalSubmissionRequest,
): Promise<PreArrivalSubmissionResult> {
  const response = await fetch(`${API_BASE_URL}/patient/pre-arrival/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? "The clinic service could not process this submission.");
  }

  return response.json() as Promise<PreArrivalSubmissionResult>;
}
