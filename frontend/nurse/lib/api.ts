import { demoSnapshot } from "./demo-data";
import type { ActionResult, DashboardSnapshot, ReadinessState, SimulatorSnapshot } from "@epicenter/shared/contracts";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
type AccessTokenProvider = () => Promise<string | null>;

type ReverificationHint = {
  clerk_error: {
    type: "forbidden";
    reason: "reverification-error";
    metadata: { reverification: string | { level: string; afterMinutes: number } };
  };
};

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

function isReverificationHint(value: unknown): value is ReverificationHint {
  if (!value || typeof value !== "object" || !("clerk_error" in value)) return false;
  const clerkError = (value as ReverificationHint).clerk_error;
  return clerkError?.type === "forbidden" && clerkError.reason === "reverification-error";
}

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
    const body = await response.json().catch(() => ({ detail: "Request failed" }));
    if (isReverificationHint(body)) return body as T;
    throw new ApiError(typeof body.detail === "string" ? body.detail : "Request failed", response.status);
  }
  return response.json() as Promise<T>;
}

export async function fetchDashboard(): Promise<{ data: DashboardSnapshot; source: "api" | "fallback" }> {
  try {
    return { data: await request<DashboardSnapshot>("/dashboard"), source: "api" };
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) throw error;
    return { data: demoSnapshot, source: "fallback" };
  }
}

export function fetchStaffSession() {
  return request<{ role: string; clinic_id: string }>("/staff/session");
}

export function transitionTicket(ticketId: string, expectedVersion: number, readinessState: ReadinessState, reason: string, staffConfirmed: boolean) {
  return request<ActionResult>(`/tickets/${ticketId}/transition`, {
    method: "POST",
    body: JSON.stringify({ readiness_state: readinessState, reason, staff_confirmed: staffConfirmed, expected_version: expectedVersion, idempotency_key: crypto.randomUUID() }),
  });
}

export function decideRecommendation(recommendationId: string, expectedVersion: number, decision: "approved" | "rejected") {
  return request<ActionResult>(`/recommendations/${recommendationId}/decision`, {
    method: "POST",
    body: JSON.stringify({ decision, expected_version: expectedVersion, idempotency_key: crypto.randomUUID() }),
  });
}

export function checkInWalkIn(patientName: string, nurseSupervisor: string, clinicalEscalation: boolean) {
  return request<ActionResult>("/kiosk/check-in", {
    method: "POST",
    body: JSON.stringify({ patient_name: patientName, nurse_supervisor: nurseSupervisor, clinical_escalation: clinicalEscalation, idempotency_key: crypto.randomUUID() }),
  });
}

export async function fetchSimulatorSnapshots(): Promise<SimulatorSnapshot[] | null> {
  try {
    return await request<SimulatorSnapshot[]>("/simulator/snapshots");
  } catch {
    return null;
  }
}
