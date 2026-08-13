import type {
  MockPaymentRequest,
  OnboardingAdvanceRequest,
  PatientAccountSession,
  PatientHome,
  PatientOnboardingState,
  PatientPaymentSummary,
  PatientQuestionnaire,
  PatientQueueStatus,
  PatientVisitHistory,
  PreArrivalSubmissionRequest,
  PreArrivalSubmissionResult,
  PriorCoverageSummary,
  QuestionnaireSaveRequest,
  UploadLinkSession,
} from "@epicenter/shared/contracts";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
type AccessTokenProvider = () => Promise<string | null>;

let accessTokenProvider: AccessTokenProvider | null = null;

class PatientApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = "PatientApiError";
  }
}

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
    throw new PatientApiError(body?.detail ?? "The clinic service could not process this request.", response.status);
  }
  return response.json() as Promise<T>;
}

export function activatePatientAccount(): Promise<PatientAccountSession> {
  return request("/patient/account/activate", { method: "POST" });
}

export function getOnboardingState(): Promise<PatientOnboardingState> {
  return request("/patient/onboarding");
}

export function advanceOnboarding(payload: OnboardingAdvanceRequest): Promise<PatientOnboardingState> {
  return request("/patient/onboarding/advance", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getPatientHome(): Promise<PatientHome> {
  return request("/patient/home");
}

export function getPriorCoverage(
  appointmentId: string,
  options?: { firstVisit?: boolean },
): Promise<PriorCoverageSummary> {
  const params = new URLSearchParams({ appointment_id: appointmentId });
  if (options?.firstVisit) params.set("first_visit", "true");
  return request(`/patient/coverage/prior?${params.toString()}`);
}

export function getPatientQueue(): Promise<PatientQueueStatus> {
  return request("/patient/queue");
}

export function getPatientPayment(): Promise<PatientPaymentSummary> {
  return request("/patient/payment");
}

export function submitMockPayment(payload: MockPaymentRequest): Promise<PatientPaymentSummary> {
  return request("/patient/payment/mock-pay", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getPatientRecords(): Promise<PatientVisitHistory> {
  return request("/patient/records");
}

export async function getPatientQuestionnaire(appointmentId: string): Promise<PatientQuestionnaire> {
  const path = `/patient/questionnaire?appointment_id=${encodeURIComponent(appointmentId)}`;
  let lastError: unknown;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      return await request(path);
    } catch (error) {
      lastError = error;
      const retryable =
        !(error instanceof PatientApiError) || error.status === 409 || error.status === 429 || error.status >= 500;
      if (!retryable || attempt === 2) throw error;
      await new Promise((resolve) => window.setTimeout(resolve, 200 * (attempt + 1)));
    }
  }
  throw lastError;
}

export function savePatientQuestionnaire(payload: QuestionnaireSaveRequest): Promise<PatientQuestionnaire> {
  return request("/patient/questionnaire", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function resolveUploadLink(token: string): Promise<UploadLinkSession> {
  return request(`/patient/upload-links/${encodeURIComponent(token)}`);
}

export async function submitPreArrival(
  payload: PreArrivalSubmissionRequest,
): Promise<PreArrivalSubmissionResult> {
  return request("/patient/pre-arrival/submit", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function submitOnboardingCoverage(payload: {
  file_name: string;
  idempotency_key: string;
}): Promise<PreArrivalSubmissionResult> {
  return request("/patient/onboarding/coverage", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
