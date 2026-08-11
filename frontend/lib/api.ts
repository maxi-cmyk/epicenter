import { demoSnapshot } from "./demo-data";
import type { ActionResult, DashboardSnapshot, ReadinessState } from "./types";

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
    const body = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(body.detail ?? "Request failed");
  }
  return response.json() as Promise<T>;
}

export async function fetchDashboard(): Promise<{ data: DashboardSnapshot; source: "api" | "fallback" }> {
  try {
    return { data: await request<DashboardSnapshot>("/dashboard"), source: "api" };
  } catch {
    return { data: demoSnapshot, source: "fallback" };
  }
}

export function transitionTicket(ticketId: string, readinessState: ReadinessState, reason: string, staffConfirmed: boolean) {
  return request<ActionResult>(`/tickets/${ticketId}/transition`, {
    method: "POST",
    body: JSON.stringify({ readiness_state: readinessState, reason, staff_confirmed: staffConfirmed }),
  });
}

export function decideRecommendation(recommendationId: string, decision: "approved" | "rejected") {
  return request<ActionResult>(`/recommendations/${recommendationId}/decision`, {
    method: "POST",
    body: JSON.stringify({ decision }),
  });
}

export function checkInWalkIn(patientName: string, nurseSupervisor: string, clinicalEscalation: boolean) {
  return request<ActionResult>("/kiosk/check-in", {
    method: "POST",
    body: JSON.stringify({ patient_name: patientName, nurse_supervisor: nurseSupervisor, clinical_escalation: clinicalEscalation }),
  });
}
