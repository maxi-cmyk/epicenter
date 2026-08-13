"use client";

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

export function QuestionnaireWorkspace({
  embedded = false,
  appointmentId = DEFAULT_APPOINTMENT_ID,
  onSubmitted,
}: QuestionnaireWorkspaceProps) {
  const [form, setForm] = useState<PatientQuestionnaire | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [acknowledged, setAcknowledged] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
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

  async function persist(submit: boolean) {
    if (!form) return;
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
      if (submit) onSubmitted?.();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to save the questionnaire.");
    } finally {
      setSaving(false);
    }
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

  return (
    <div className={embedded ? undefined : styles.page}>
      {!embedded ? (
        <PageHeader
          description="Parkway General Health Screening fields with conditional follow-ups. Singpass identity stays read-only."
          title={form.title}
        />
      ) : null}
      <section className={styles.panel}>
        <div className={styles.prefillList}>
          {form.prefill.map((field) => (
            <div key={field.field_id}>
              <dt>{field.label}</dt>
              <dd>{field.value}</dd>
              <small className={styles.muted}>Source: {field.source}</small>
            </div>
          ))}
        </div>

        {sections.map(({ section, fields }) => (
          <div className={styles.fieldStack} key={section}>
            <h3 className={styles.statusHero} style={{ fontSize: "1.35rem", margin: "8px 0 0" }}>
              <strong>{section}</strong>
            </h3>
            {fields.map((field) => (
              <label key={field.field_id}>
                <span>
                  {field.label}
                  {field.required ? " *" : ""}
                </span>
                {field.help_text ? <small className={styles.muted}>{field.help_text}</small> : null}
                {field.field_type === "select" ? (
                  <select
                    disabled={form.status === "submitted"}
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
                            disabled={form.status === "submitted"}
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
                    disabled={form.status === "submitted"}
                    onChange={(event) => updateAnswer(field.field_id, event.target.value)}
                    type="text"
                    value={answers[field.field_id] ?? ""}
                  />
                ) : (
                  <textarea
                    disabled={form.status === "submitted"}
                    onChange={(event) => updateAnswer(field.field_id, event.target.value)}
                    value={answers[field.field_id] ?? ""}
                  />
                )}
              </label>
            ))}
          </div>
        ))}

        <label className={styles.checkboxRow}>
          <input
            checked={acknowledged}
            disabled={form.status === "submitted"}
            onChange={(event) => setAcknowledged(event.target.checked)}
            type="checkbox"
          />
          <span>
            I acknowledge the declaration for collection, use and disclosure of personal data for this health screening
            questionnaire.
          </span>
        </label>

        {form.status !== "submitted" ? (
          <div className={styles.uploadActions}>
            <Button disabled={saving} onClick={() => void persist(false)} variant="secondary">
              {saving ? "Saving…" : "Save draft"}
            </Button>
            <Button disabled={saving} onClick={() => void persist(true)}>
              {saving ? "Submitting…" : "Submit questionnaire"}
            </Button>
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
