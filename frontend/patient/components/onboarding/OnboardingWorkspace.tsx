"use client";

import { Check, FileCheck2, LockKeyhole, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";

import { Button } from "@epicenter/shared/ui/Button";
import { PageHeader } from "@epicenter/shared/ui/PageHeader";
import type { PatientOnboardingState, SingpassProfileField } from "@epicenter/shared/contracts";

import { CoverageWorkspace } from "@/components/coverage/CoverageWorkspace";
import { QuestionnaireWorkspace } from "@/components/questionnaire/QuestionnaireWorkspace";
import { advanceOnboarding, getOnboardingState } from "@/lib/api";
import { useMountedLoad } from "@/lib/useMountedLoad";

import styles from "./Onboarding.module.css";

const STEPS = [
  { id: "singpass", label: "Singpass profile" },
  { id: "insurance", label: "Insurance" },
  { id: "questionnaire", label: "Questionnaire" },
] as const;

type StepId = (typeof STEPS)[number]["id"];

export function OnboardingWorkspace() {
  const router = useRouter();
  const [state, setState] = useState<PatientOnboardingState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [coverageSubmitted, setCoverageSubmitted] = useState(false);
  const [draftFields, setDraftFields] = useState<SingpassProfileField[]>([]);
  const [reviewingStep, setReviewingStep] = useState<StepId | null>(null);

  const load = useCallback(async () => {
    try {
      const next = await getOnboardingState();
      setState(next);
      setDraftFields(next.singpass_fields);
      setReviewingStep(null);
      if (next.completed) router.replace("/");
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to open onboarding.");
    }
  }, [router]);

  useMountedLoad(load);

  async function continueFrom(
    step: "singpass" | "insurance" | "questionnaire",
    extra: Record<string, boolean>,
    fields?: SingpassProfileField[],
  ) {
    setBusy(true);
    setError(null);
    try {
      const next = await advanceOnboarding({
        step,
        idempotency_key: crypto.randomUUID(),
        ...(fields ? { singpass_fields: fields } : {}),
        ...extra,
      });
      setState(next);
      setDraftFields(next.singpass_fields);
      if (next.completed) router.replace("/");
    } catch (advanceError) {
      setError(advanceError instanceof Error ? advanceError.message : "Could not continue onboarding.");
    } finally {
      setBusy(false);
    }
  }

  function updateField(fieldId: string, value: string) {
    setDraftFields((current) =>
      current.map((field) => (field.field_id === fieldId ? { ...field, value } : field)),
    );
  }

  if (!state) {
    return (
      <div aria-busy="true" className={styles.page}>
        <div className={styles.skeleton} />
      </div>
    );
  }

  const canConfirmSingpass =
    draftFields.length > 0 && draftFields.every((field) => field.value.trim().length > 0);
  const currentIndex = STEPS.findIndex((item) => item.id === state.current_step);
  const onboardingState = state;

  function stepIsDone(step: StepId) {
    return (
      onboardingState.completed ||
      (step === "singpass" && onboardingState.singpass_authenticated && currentIndex > 0) ||
      (step === "insurance" && onboardingState.insurance_completed) ||
      (step === "questionnaire" && onboardingState.questionnaire_completed)
    );
  }

  return (
    <div className={styles.page}>
      <PageHeader
        description="First-time patients complete Singpass profile confirmation, coverage, and the General Health Screening questionnaire before the clinic visit."
        title="Prepare for your visit"
      />

      <ol className={styles.stepper} aria-label="Onboarding steps">
        {STEPS.map((step, index) => {
          const done = stepIsDone(step.id);
          const active = step.id === state.current_step;
          const canOpenStep = (done && !active) || (active && reviewingStep !== null);
          return (
            <li className={active ? styles.activeStep : done ? styles.doneStep : undefined} key={step.id}>
              {canOpenStep ? (
                <button onClick={() => setReviewingStep(active ? null : step.id)} type="button">
                  <span>{done ? <Check aria-hidden="true" size={14} /> : index + 1}</span>
                  {step.label}
                  <small>{active ? "Return" : "Review"}</small>
                </button>
              ) : (
                <div>
                  <span>{done ? <Check aria-hidden="true" size={14} /> : index + 1}</span>
                  {step.label}
                </div>
              )}
            </li>
          );
        })}
      </ol>

      {reviewingStep ? (
        <section className={styles.reviewPanel}>
          <div className={styles.inlineTitle}>
            {reviewingStep === "singpass" ? <LockKeyhole aria-hidden="true" size={22} /> : <FileCheck2 aria-hidden="true" size={22} />}
            <div>
              <strong>{reviewingStep === "singpass" ? "Singpass profile saved" : "Coverage saved"}</strong>
              <p>
                {reviewingStep === "singpass"
                  ? "These details were saved from the synthetic Singpass/Myinfo step. Staff still verify identity and e-card details in person."
                  : "Your coverage document was received for staff review. This does not confirm eligibility or payment approval."}
              </p>
            </div>
          </div>
          {reviewingStep === "singpass" ? (
            <dl className={styles.fieldGrid}>
              {draftFields.map((field) => (
                <div key={field.field_id}>
                  <dt>{field.label}</dt>
                  <dd>{field.value || "—"}</dd>
                  <small>{field.source}</small>
                </div>
              ))}
            </dl>
          ) : null}
          <Button onClick={() => setReviewingStep(null)} variant="secondary">Return to current step</Button>
        </section>
      ) : null}

      {!reviewingStep && state.current_step === "singpass" ? (
        <section className={styles.panel}>
          <div className={styles.singpassBand}>
            <LockKeyhole aria-hidden="true" size={24} />
            <div>
              <strong>Singpass Login / Myinfo</strong>
              <span>Synthetic adapter — exact field autofill only. No live Singpass sandbox is connected.</span>
            </div>
          </div>
          <p className={styles.note}>
            Retrieve consented personal particulars once, then reuse them across registration and the questionnaire.
            Staff still complete identity and e-card checks in person on arrival.
          </p>
          {!state.singpass_authenticated ? (
            <Button
              aria-label="Log in with Singpass"
              className={styles.singpassLoginButton}
              disabled={busy}
              onClick={() => void continueFrom("singpass", { singpass_authenticated: true })}
            >
              {busy ? (
                "Connecting…"
              ) : (
                <>
                  Log in with <span className={styles.singpassWordmark}><span>Sing</span>pass</span>
                </>
              )}
            </Button>
          ) : (
            <>
              <dl className={styles.fieldGrid}>
                {draftFields.map((field) => (
                  <div key={field.field_id}>
                    <dt>{field.label}</dt>
                    {field.editable ? (
                      <dd>
                        <input
                          aria-label={field.label}
                          className={styles.fieldInput}
                          onChange={(event) => updateField(field.field_id, event.target.value)}
                          value={field.value}
                        />
                      </dd>
                    ) : (
                      <dd>{field.value || "—"}</dd>
                    )}
                    <small>{field.source}</small>
                  </div>
                ))}
              </dl>
              <Button
                disabled={busy || (draftFields.some((field) => field.editable) && !canConfirmSingpass)}
                onClick={() =>
                  void continueFrom("singpass", { singpass_authenticated: true }, draftFields)
                }
              >
                {busy ? "Saving…" : "Confirm details and continue"}
              </Button>
            </>
          )}
        </section>
      ) : null}

      {!reviewingStep && state.current_step === "insurance" ? (
        <section className={styles.panel}>
          <div className={styles.inlineTitle}>
            <FileCheck2 aria-hidden="true" size={22} />
            <div>
              <strong>Insurance / coverage</strong>
              <p>First-time patients have no prior policy on file. Upload your coverage document for this visit.</p>
            </div>
          </div>
          <CoverageWorkspace
            embedded
            firstTime
            onSubmitted={() => setCoverageSubmitted(true)}
          />
          <Button
            disabled={busy || !coverageSubmitted}
            onClick={() => void continueFrom("insurance", { insurance_completed: true })}
          >
            {busy ? "Saving…" : coverageSubmitted ? "Coverage uploaded — continue" : "Upload coverage to continue"}
          </Button>
        </section>
      ) : null}

      {!reviewingStep && state.current_step === "questionnaire" ? (
        <section className={styles.panel}>
          <div className={styles.inlineTitle}>
            <ShieldCheck aria-hidden="true" size={22} />
            <div>
              <strong>General Health Screening Questionnaire</strong>
              <p>
                Your Singpass profile is already applied. Answer only the standard health screening questions.
              </p>
            </div>
          </div>
          <QuestionnaireWorkspace
            appointmentId={
              !state.appointment_id ||
              state.appointment_id === "pending-booking" ||
              state.appointment_id === "PENDING" ||
              state.appointment_id === "APT-DEMO-014"
                ? "pending-booking"
                : state.appointment_id
            }
            embedded
            onSubmitted={() => void continueFrom("questionnaire", { questionnaire_completed: true })}
          />
        </section>
      ) : null}

      {error ? (
        <div className={styles.error} role="alert">
          {error}
        </div>
      ) : null}
    </div>
  );
}
