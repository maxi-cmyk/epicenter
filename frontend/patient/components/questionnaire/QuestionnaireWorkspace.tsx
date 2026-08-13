"use client";

import { ArrowLeft, Check, ChevronRight, ShieldAlert } from "lucide-react";
import Link from "next/link";
import { useCallback, useMemo, useState } from "react";

import { Button } from "@epicenter/shared/ui/Button";
import { PageHeader } from "@epicenter/shared/ui/PageHeader";
import type { PatientQuestionnaire } from "@epicenter/shared/contracts";

import { getPatientQuestionnaire, savePatientQuestionnaire } from "@/lib/api";
import { useMountedLoad } from "@/lib/useMountedLoad";

import styles from "../home/Journey.module.css";

const DEFAULT_APPOINTMENT_ID = "pending-booking";

type QuestionnaireWorkspaceProps = {
  embedded?: boolean;
  appointmentId?: string;
  onSubmitted?: () => void;
  startInEditMode?: boolean;
};

type Field = PatientQuestionnaire["fields"][number];

function selectedValues(raw: string | undefined): string[] {
  return (raw ?? "")
    .split("|")
    .map((value) => value.trim())
    .filter(Boolean);
}

function conditionMatches(raw: string, expected: string | null | undefined, mode: string | null | undefined) {
  const normalized = raw.trim();
  const target = expected ?? "";
  const matchMode = mode ?? "equals";
  if (matchMode === "not_empty") return normalized.length > 0;
  if (matchMode === "contains") {
    return selectedValues(normalized).includes(target);
  }
  if (matchMode === "any_of") {
    return target.split("|").map((part) => part.trim()).filter(Boolean).includes(normalized);
  }
  return normalized === target;
}

function isFieldVisible(field: Field, answers: Record<string, string>) {
  if (field.show_if_field) {
    if (!conditionMatches(answers[field.show_if_field] ?? "", field.show_if_value, field.show_if_mode)) {
      return false;
    }
  }
  if (field.show_if_field_2) {
    if (!conditionMatches(answers[field.show_if_field_2] ?? "", field.show_if_value_2, field.show_if_mode_2)) {
      return false;
    }
  }
  return true;
}

function hasAnswer(field: Field, answers: Record<string, string>) {
  return !field.required || Boolean(answers[field.field_id]?.trim());
}

function displayAnswer(field: Field, answers: Record<string, string>) {
  return answers[field.field_id]?.trim().replaceAll("|", ", ") || "—";
}

export function QuestionnaireWorkspace({
  embedded = false,
  appointmentId = DEFAULT_APPOINTMENT_ID,
  onSubmitted,
  startInEditMode = false,
}: QuestionnaireWorkspaceProps) {
  const [form, setForm] = useState<PatientQuestionnaire | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [acknowledged, setAcknowledged] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [sectionIndex, setSectionIndex] = useState(0);
  const [reviewing, setReviewing] = useState(false);
  const [editingSubmitted, setEditingSubmitted] = useState(startInEditMode);
  const [viewingSubmittedSection, setViewingSubmittedSection] = useState(false);
  const resolvedAppointmentId =
    !appointmentId || appointmentId === "pending-booking" ? DEFAULT_APPOINTMENT_ID : appointmentId;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const questionnaire = await getPatientQuestionnaire(resolvedAppointmentId);
      setForm(questionnaire);
      const nextAnswers = Object.fromEntries(
        questionnaire.fields
          .filter((field) => field.value)
          .map((field) => [field.field_id, field.value as string]),
      );
      if (!nextAnswers.gender) {
        const sex = questionnaire.prefill.find((field) => field.field_id === "sex" || field.field_id === "gender");
        if (sex?.value) nextAnswers.gender = sex.value;
      }
      setAnswers(nextAnswers);
      setAcknowledged(questionnaire.declaration_acknowledged);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load the questionnaire.");
    } finally {
      setLoading(false);
    }
  }, [resolvedAppointmentId]);

  useMountedLoad(load);

  const visibleFields = useMemo(() => {
    if (!form) return [];
    return form.fields.filter((field) => isFieldVisible(field, answers));
  }, [answers, form]);

  const sections = useMemo(() => {
    const order: string[] = [];
    const grouped = new Map<string, Field[]>();
    for (const field of visibleFields) {
      const section = field.section ?? "Additional details";
      if (!grouped.has(section)) {
        grouped.set(section, []);
        order.push(section);
      }
      grouped.get(section)?.push(field);
    }
    return order.map((section) => ({ section, fields: grouped.get(section) ?? [] }));
  }, [visibleFields]);

  async function reloadWithAnswers(nextAnswers: Record<string, string>) {
    // Gender/provider changes alter available medical options; refresh catalog from API after save draft.
    setAnswers(nextAnswers);
    try {
      const saved = await savePatientQuestionnaire({
        appointment_id: resolvedAppointmentId,
        answers: nextAnswers,
        declaration_acknowledged: acknowledged,
        submit: false,
        expected_version: form?.version ?? 1,
        idempotency_key: crypto.randomUUID(),
      });
      setForm(saved);
    } catch {
      // Keep local answers if draft refresh fails; submit will still validate.
    }
  }

  async function persist(submit: boolean): Promise<boolean> {
    if (!form) return false;
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const saved = await savePatientQuestionnaire({
        appointment_id: resolvedAppointmentId,
        answers,
        declaration_acknowledged: acknowledged,
        submit,
        expected_version: form.version,
        idempotency_key: crypto.randomUUID(),
      });
      setForm(saved);
      setMessage(submit ? "Questionnaire submitted for this appointment." : "Draft saved.");
      if (submit) {
        setEditingSubmitted(false);
        onSubmitted?.();
      }
      return true;
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to save the questionnaire.");
      return false;
    } finally {
      setSaving(false);
    }
  }

  async function continueTo(nextIndex: number) {
    if (form?.status !== "submitted" && !(await persist(false))) return;
    setSectionIndex(nextIndex);
    setReviewing(false);
  }

  async function openReview() {
    if (form?.status !== "submitted" && !(await persist(false))) return;
    setReviewing(true);
  }

  async function submitFromReview() {
    const incompleteSectionIndex = sections.findIndex(({ fields }) =>
      fields.some((field) => !hasAnswer(field, answers)),
    );
    if (incompleteSectionIndex >= 0) {
      const missing = sections[incompleteSectionIndex].fields.filter((field) => !hasAnswer(field, answers)).length;
      setError(
        `Complete ${missing} required ${missing === 1 ? "question" : "questions"} in ${sections[incompleteSectionIndex].section} before submitting.`,
      );
      setSectionIndex(incompleteSectionIndex);
      setReviewing(false);
      return;
    }
    await persist(true);
  }

  function toggleMulti(fieldId: string, option: string) {
    const current = new Set(selectedValues(answers[fieldId]));
    if (current.has(option)) current.delete(option);
    else current.add(option);
    const next = { ...answers, [fieldId]: Array.from(current).join("|") };
    setAnswers(next);
  }

  function updateAnswer(fieldId: string, value: string) {
    const next = { ...answers, [fieldId]: value };
    setAnswers(next);
    if (fieldId === "gender" || fieldId === "screening_provider") {
      void reloadWithAnswers(next);
    }
  }

  if (loading && !form) {
    return (
      <div aria-busy="true" className={embedded ? undefined : styles.page}>
        <div className={styles.skeletonCard} />
      </div>
    );
  }

  if (!form) {
    return (
      <div className={embedded ? undefined : styles.page} role="alert">
        {!embedded ? <PageHeader description={error ?? "Questionnaire unavailable."} title="Questionnaire" /> : null}
        {embedded ? (
          <div className={styles.errorBox}>
            {error ?? "The questionnaire could not be loaded automatically."}
          </div>
        ) : null}
        <Button onClick={() => void load()}>Retry</Button>
      </div>
    );
  }

  const safeSectionIndex = Math.min(sectionIndex, Math.max(sections.length - 1, 0));
  const activeSection = sections[safeSectionIndex];
  const requiredFields = visibleFields.filter((field) => field.required);
  const completedRequired = requiredFields.filter((field) => hasAnswer(field, answers)).length;
  const canEdit = form.status !== "submitted" || editingSubmitted;
  const showingReview = reviewing || (!canEdit && !viewingSubmittedSection);

  return (
    <div className={embedded ? undefined : `${styles.page} ${styles.questionnairePage}`}>
      {!embedded ? (
        <PageHeader
          description="Your Singpass profile is already applied. Answer only the health screening questions."
          title={
            <>
              <span className={styles.questionnaireTitleLine}>General Health</span>{" "}
              <span className={styles.questionnaireTitleLine}>Screening Questionnaire</span>
            </>
          }
        />
      ) : null}
      <section className={`${styles.panel} ${embedded ? styles.embeddedQuestionnaire : ""}`}>
        <div className={styles.clinicalSafety} role="note">
          <ShieldAlert aria-hidden="true" size={22} />
          <div>
            <strong>This questionnaire does not assess medical urgency.</strong>
            <span>
              Tell clinic staff immediately about urgent symptoms. Clinical care always takes priority and paperwork
              will not delay escalation.
            </span>
          </div>
        </div>

        <div className={styles.questionnaireProgress}>
          <div>
            <strong>{showingReview ? "Review answers" : `Section ${safeSectionIndex + 1} of ${sections.length}`}</strong>
            <span>
              {completedRequired} of {requiredFields.length} required questions complete
            </span>
          </div>
          <progress aria-label="Required questionnaire questions completed" max={requiredFields.length || 1} value={completedRequired} />
        </div>

        <nav aria-label="Questionnaire sections" className={styles.questionnaireSections}>
          {sections.map(({ section, fields }, index) => {
            const complete = fields.every((field) => hasAnswer(field, answers));
            const active = !showingReview && index === safeSectionIndex;
            return (
              <button
                aria-current={active ? "step" : undefined}
                className={active ? styles.questionnaireSectionActive : undefined}
                disabled={saving}
                key={section}
                onClick={() => {
                  if (canEdit) {
                    void continueTo(index);
                    return;
                  }
                  setSectionIndex(index);
                  setReviewing(false);
                  setViewingSubmittedSection(true);
                }}
                type="button"
              >
                <span>{complete ? <Check aria-hidden="true" size={14} /> : index + 1}</span>
                {section}
              </button>
            );
          })}
          <button
            aria-current={showingReview ? "step" : undefined}
            className={showingReview ? styles.questionnaireSectionActive : undefined}
            disabled={saving}
            onClick={() => {
              setViewingSubmittedSection(false);
              if (canEdit) {
                void openReview();
                return;
              }
              setReviewing(true);
            }}
            type="button"
          >
            <span>{sections.length + 1}</span>
            Review
          </button>
        </nav>

        {!showingReview && activeSection ? (
          <div className={styles.fieldStack} key={activeSection.section}>
            <div className={styles.sectionHeading}>
              <h3>{activeSection.section}</h3>
              <span>
                Required questions are marked <span className={styles.requiredMark}>*</span>
              </span>
            </div>
            {activeSection.fields.map((field) => (
              <label key={field.field_id}>
                <span>
                  {field.label}
                  {field.required ? <span aria-hidden="true" className={styles.requiredMark}> *</span> : null}
                </span>
                {field.help_text ? <small className={styles.muted}>{field.help_text}</small> : null}
                {field.field_type === "select" ? (
                  <select
                    disabled={!canEdit}
                    onChange={(event) => updateAnswer(field.field_id, event.target.value)}
                    value={answers[field.field_id] ?? ""}
                  >
                    <option value="">Select one</option>
                    {field.options?.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                ) : field.field_type === "multiselect" ? (
                  <div className={styles.checkGrid}>
                    {field.options?.map((option) => {
                      const checked = selectedValues(answers[field.field_id]).includes(option);
                      return (
                        <label className={styles.checkOption} key={option}>
                          <input
                            checked={checked}
                            disabled={!canEdit}
                            onChange={() => toggleMulti(field.field_id, option)}
                            type="checkbox"
                          />
                          <span>{option}</span>
                        </label>
                      );
                    })}
                  </div>
                ) : field.field_type === "text" ? (
                  <input
                    disabled={!canEdit}
                    onChange={(event) => updateAnswer(field.field_id, event.target.value)}
                    type="text"
                    value={answers[field.field_id] ?? ""}
                  />
                ) : (
                  <textarea
                    disabled={!canEdit}
                    onChange={(event) => updateAnswer(field.field_id, event.target.value)}
                    value={answers[field.field_id] ?? ""}
                  />
                )}
              </label>
            ))}
          </div>
        ) : null}

        {showingReview ? (
          <div className={styles.questionnaireReview}>
            <div className={styles.sectionHeading}>
              <h3>Check your answers</h3>
              <span>Review each section before submitting the standard questionnaire.</span>
            </div>
            {sections.map(({ section, fields }, index) => (
              <section key={section}>
                <header>
                  <h4>{section}</h4>
                  {canEdit ? (
                    <button
                      onClick={() => {
                        setSectionIndex(index);
                        setReviewing(false);
                      }}
                      type="button"
                    >
                      Edit
                    </button>
                  ) : null}
                </header>
                <dl>
                  {fields.map((field) => (
                    <div key={field.field_id}>
                      <dt>{field.label}</dt>
                      <dd>{displayAnswer(field, answers)}</dd>
                    </div>
                  ))}
                </dl>
              </section>
            ))}
            <label className={styles.checkboxRow}>
              <input
                checked={acknowledged}
                disabled={!canEdit}
                onChange={(event) => setAcknowledged(event.target.checked)}
                type="checkbox"
              />
              <span>
                I acknowledge the declaration for collection, use and disclosure of personal data for this health
                screening questionnaire.
              </span>
            </label>
          </div>
        ) : null}

        {canEdit ? (
          <div className={styles.questionnaireActions}>
            <div className={styles.questionnaireActionStart}>
              {!embedded ? (
                <Link className={styles.questionnaireBackLink} href="/">
                  <ArrowLeft aria-hidden="true" size={18} />
                  Back to home
                </Link>
              ) : null}
              {!showingReview && safeSectionIndex > 0 ? (
                <Button
                  disabled={saving}
                  onClick={() => void continueTo(Math.max(0, safeSectionIndex - 1))}
                  variant="quiet"
                >
                  Previous section
                </Button>
              ) : null}
            </div>
            <div>
              <Button disabled={saving} onClick={() => void persist(false)} variant="secondary">
                {saving ? "Saving…" : "Save draft"}
              </Button>
              {showingReview ? (
                <Button disabled={saving || !acknowledged} onClick={() => void submitFromReview()}>
                  {saving ? "Submitting…" : "Submit questionnaire"}
                </Button>
              ) : safeSectionIndex === sections.length - 1 ? (
                <Button disabled={saving} onClick={() => void openReview()}>
                  {saving ? "Saving…" : "Review answers"}
                </Button>
              ) : (
                <Button
                  disabled={saving}
                  icon={<ChevronRight aria-hidden="true" size={17} />}
                  onClick={() => void continueTo(safeSectionIndex + 1)}
                >
                  {saving ? "Saving…" : "Save and continue"}
                </Button>
              )}
            </div>
          </div>
        ) : (
          <div className={styles.successBox} role="status">
            <strong>Submitted</strong>
            <span>
              {embedded
                ? "Questionnaire saved for onboarding."
                : "You can continue to queue status. Staff still confirm the visit outcome."}
            </span>
            {!embedded ? <Link href="/queue">View queue</Link> : null}
          </div>
        )}

        {message ? (
          <div className={styles.successBox} role="status">
            {message}
          </div>
        ) : null}
        {error ? (
          <div className={styles.errorBox} role="alert">
            {error}
          </div>
        ) : null}
      </section>
    </div>
  );
}
