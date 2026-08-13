import type { ActionResult, AuditRecord, MedicationItem, PatientList, QueueTicket, TpaSubmission } from "@epicenter/shared/contracts";
import type { AuditQuery } from "@epicenter/shared/ui/AuditPanel";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
type AccessTokenProvider = (options?: { skipCache?: boolean }) => Promise<string | null>;

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

export async function refreshAccessToken() {
  await accessTokenProvider?.({ skipCache: true });
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

export function fetchStaffSession() {
  return request<{ role: string; clinic_id: string }>("/staff/session");
}

export function fetchAudit(query: AuditQuery) {
  const params = new URLSearchParams({ limit: String(query.limit), offset: String(query.offset) });
  if (query.search) params.set("search", query.search);
  if (query.actor) params.set("actor", query.actor);
  if (query.actorRole) params.set("actor_role", query.actorRole);
  if (query.outcome) params.set("outcome", query.outcome);
  if (query.actionType) params.set("action_type", query.actionType);
  if (query.targetTable) params.set("target_table", query.targetTable);
  if (query.occurredFrom) params.set("occurred_from", query.occurredFrom);
  if (query.occurredTo) params.set("occurred_to", query.occurredTo);
  return request<AuditRecord[]>(`/audit?${params.toString()}`, { cache: "no-store" });
}

export function fetchPatients(query: { search?: string; contactFilter?: string; sort?: string; offset: number; limit: number }) {
  const params = new URLSearchParams({ offset: String(query.offset), limit: String(query.limit) });
  if (query.search) params.set("search", query.search);
  if (query.contactFilter) params.set("contact_filter", query.contactFilter);
  if (query.sort) params.set("sort", query.sort);
  return request<PatientList>(`/patients?${params.toString()}`, { cache: "no-store" });
}

export function fetchPharmacyQueue() {
  return request<QueueTicket[]>("/pharmacy/queue");
}

export function recordMedicationDispense(ticketId: string, items: MedicationItem[]) {
  return request<ActionResult>(`/tickets/${ticketId}/medication`, {
    method: "POST",
    body: JSON.stringify({ items, idempotency_key: crypto.randomUUID() }),
  });
}

export function fetchTpaSubmission(ticketId: string) {
  return request<TpaSubmission>(`/tickets/${ticketId}/tpa-submission`);
}

export function confirmTpaSubmission(ticketId: string, expectedVersion: number) {
  return request<ActionResult>(`/tickets/${ticketId}/tpa-submission/confirm`, {
    method: "POST",
    body: JSON.stringify({ expected_version: expectedVersion, idempotency_key: crypto.randomUUID() }),
  });
}
