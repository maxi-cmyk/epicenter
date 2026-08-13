"use client";

import type { AuditRecord } from "../contracts";
import { Download, Search, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "./PageHeader";
import styles from "./AuditPanel.module.css";

export type AuditQuery = {
  search?: string;
  actor?: string;
  actorRole?: string;
  outcome?: string;
  actionType?: string;
  targetTable?: string;
  occurredFrom?: string;
  occurredTo?: string;
  offset: number;
  limit: number;
};

type Props = {
  loadAudit: (query: AuditQuery) => Promise<AuditRecord[]>;
};

const PAGE_SIZE = 20;

const ACTION_LABELS: Record<string, string> = {
  medication_dispensed: "Medication dispensed",
  tpa_submission_confirmed: "TPA submitted",
  payment_details_confirmed: "Payment details confirmed",
  visit_checked_in: "Visit checked in",
  visit_completed: "Visit completed",
  ticket_transitioned: "Readiness changed",
  patient_created: "Patient created",
  patient_updated: "Patient updated",
  patient_soft_deleted: "Patient archived",
};

function titleCase(value: string) {
  return ACTION_LABELS[value] ?? value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function actorRole(record: AuditRecord) {
  return record.actor_role ? titleCase(record.actor_role) : "Staff";
}

function actorLabel(actor: string) {
  if (actor.startsWith("user_")) return `Staff · ${actor.slice(-6)}`;
  return titleCase(actor.replace(/^synthetic-/, ""));
}

function outcome(record: AuditRecord) {
  const detailOutcome = record.details.outcome ?? record.details.status;
  return typeof detailOutcome === "string" ? titleCase(detailOutcome) : "Committed";
}

function detailRows(details: Record<string, unknown>, prefix = ""): Array<[string, string]> {
  return Object.entries(details).flatMap(([key, value]) => {
    const label = `${prefix}${titleCase(key)}`;
    if (value === null || value === undefined) return [];
    if (Array.isArray(value)) return [[label, value.map((item) => (typeof item === "object" ? JSON.stringify(item) : String(item))).join(" · ")]];
    if (typeof value === "object") return detailRows(value as Record<string, unknown>, `${label} · `);
    return [[label, String(value)]];
  });
}

function csvCell(value: unknown) {
  return `"${String(value ?? "").replaceAll('"', '""')}"`;
}

export function AuditPanel({ loadAudit }: Props) {
  const [search, setSearch] = useState("");
  const [actionType, setActionType] = useState("");
  const [actor, setActor] = useState("");
  const [role, setRole] = useState("");
  const [outcomeFilter, setOutcomeFilter] = useState("");
  const [targetTable, setTargetTable] = useState("");
  const [occurredFrom, setOccurredFrom] = useState("");
  const [occurredTo, setOccurredTo] = useState("");
  const [page, setPage] = useState(0);
  const [records, setRecords] = useState<AuditRecord[]>([]);
  const [selected, setSelected] = useState<AuditRecord | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);

  const query = useMemo<AuditQuery>(() => ({
    search: search.trim() || undefined,
    actor: actor || undefined,
    actorRole: role || undefined,
    outcome: outcomeFilter || undefined,
    actionType: actionType || undefined,
    targetTable: targetTable || undefined,
    occurredFrom: occurredFrom ? new Date(`${occurredFrom}T00:00:00`).toISOString() : undefined,
    occurredTo: occurredTo ? new Date(`${occurredTo}T23:59:59.999`).toISOString() : undefined,
    offset: page * PAGE_SIZE,
    limit: PAGE_SIZE + 1,
  }), [actionType, actor, occurredFrom, occurredTo, outcomeFilter, page, role, search, targetTable]);

  useEffect(() => {
    let active = true;
    const timer = window.setTimeout(() => {
      setState("loading");
      setError("");
      void loadAudit(query)
        .then((result) => {
          if (!active) return;
          setRecords(result);
          setSelected((current) => result.find((record) => record.id === current?.id) ?? null);
          setState("ready");
        })
        .catch((reason: unknown) => {
          if (!active) return;
          setRecords([]);
          setSelected(null);
          setError(reason instanceof Error ? reason.message : "Audit history could not be loaded.");
          setState("error");
        });
    }, 250);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [loadAudit, query, reload]);

  const visibleRecords = records.slice(0, PAGE_SIZE);
  const hasNext = records.length > PAGE_SIZE;
  const hasFilters = Boolean(search || actor || role || outcomeFilter || actionType || targetTable || occurredFrom || occurredTo);

  const clearFilters = () => {
    setSearch(""); setActor(""); setRole(""); setOutcomeFilter(""); setActionType(""); setTargetTable(""); setOccurredFrom(""); setOccurredTo(""); setPage(0);
  };

  const exportRecords = (format: "json" | "csv") => {
    const safeRows = visibleRecords.map((record) => ({
      occurred_at: record.occurred_at,
      actor: actorLabel(record.actor_reference),
      role: actorRole(record),
      action: titleCase(record.action_type),
      target: `${record.target_table}:${record.target_id}`,
      outcome: outcome(record),
      details: record.details,
      data_mode: "synthetic_demo",
    }));
    const content = format === "json"
      ? JSON.stringify(safeRows, null, 2)
      : [Object.keys(safeRows[0] ?? {}).map(csvCell).join(","), ...safeRows.map((row) => Object.values(row).map((value) => csvCell(typeof value === "object" ? JSON.stringify(value) : value)).join(","))].join("\n");
    const url = URL.createObjectURL(new Blob([content], { type: format === "json" ? "application/json" : "text/csv" }));
    const anchor = document.createElement("a");
    anchor.href = url; anchor.download = `epicenter-audit.${format}`; anchor.click(); URL.revokeObjectURL(url);
  };

  return (
    <section className={styles.workspace}>
      <PageHeader
        description="Audit entries cannot be edited or deleted, for viewing purposes only."
        title="Audit trail"
      />

      <div className={styles.controls}>
        <label className={styles.searchBox}>
          <span className="sr-only">Search audit trail</span><Search aria-hidden="true" size={20} />
          <input onChange={(event) => { setSearch(event.target.value); setPage(0); }} placeholder="Search actor, action, ticket, or safe event detail" type="search" value={search} />
        </label>
        <div className={styles.filters} aria-label="Audit filters">
          <label>Action<select onChange={(event) => { setActionType(event.target.value); setPage(0); }} value={actionType}><option value="">All actions</option>{Object.entries(ACTION_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          <label>Actor<select onChange={(event) => { setActor(event.target.value); setPage(0); }} value={actor}><option value="">All actors</option><option value="synthetic-staff">Clinic staff</option><option value="pharmacist">Pharmacist</option><option value="system">System</option></select></label>
          <label>Role<select onChange={(event) => { setRole(event.target.value); setPage(0); }} value={role}><option value="">All roles</option><option value="nurse">Nurse</option><option value="pharmacist">Pharmacist</option><option value="administrator">Administrator</option><option value="system">System</option></select></label>
          <label>Outcome<select onChange={(event) => { setOutcomeFilter(event.target.value); setPage(0); }} value={outcomeFilter}><option value="">All outcomes</option><option value="committed">Committed</option><option value="completed">Completed</option><option value="submitted">Submitted</option><option value="review">Review</option></select></label>
          <label>Target<select onChange={(event) => { setTargetTable(event.target.value); setPage(0); }} value={targetTable}><option value="">All targets</option><option value="queue_entries">Queue, visit &amp; payment</option><option value="medication_dispenses">Medication</option><option value="tpa_submissions">TPA submissions</option><option value="patients">Patients</option></select></label>
          <label>From<input onChange={(event) => { setOccurredFrom(event.target.value); setPage(0); }} type="date" value={occurredFrom} /></label>
          <label>To<input onChange={(event) => { setOccurredTo(event.target.value); setPage(0); }} type="date" value={occurredTo} /></label>
          {hasFilters ? <button className={styles.clearButton} onClick={clearFilters} type="button"><X aria-hidden="true" size={16} />Clear all</button> : null}
        </div>
      </div>

      <div className={styles.toolbar}>
        <p>{state === "loading" ? "Loading clinic audit history…" : state === "error" ? "Audit history unavailable" : `${visibleRecords.length} event${visibleRecords.length === 1 ? "" : "s"} on this page`}</p>
        <div><button disabled={!visibleRecords.length} onClick={() => exportRecords("csv")} type="button"><Download aria-hidden="true" size={15} />CSV</button><button disabled={!visibleRecords.length} onClick={() => exportRecords("json")} type="button"><Download aria-hidden="true" size={15} />JSON</button></div>
      </div>

      {state === "error" ? <div className={styles.message} role="alert"><strong>Audit history is unavailable</strong><p>{error}</p><button onClick={() => setReload((value) => value + 1)} type="button">Try again</button></div> : null}
      {state === "ready" && visibleRecords.length === 0 ? <div className={styles.message}><strong>No audit events found</strong><p>{hasFilters ? "Clear or adjust the active filters." : "No committed audit events are available for this clinic yet."}</p></div> : null}
      {state === "loading" ? <div className={styles.loading} role="status">Retrieving immutable events…</div> : null}

      {state === "ready" && visibleRecords.length ? <div className={styles.auditLayout}>
        <div className={styles.tableWrap}><table><thead><tr><th>Time</th><th>Actor</th><th>Role</th><th>Action</th><th>Target</th><th>Outcome</th></tr></thead><tbody>{visibleRecords.map((record) => <tr aria-selected={selected?.id === record.id} key={record.id} onClick={() => setSelected(record)} tabIndex={0} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") setSelected(record); }}><td data-label="Time"><time dateTime={record.occurred_at}>{new Intl.DateTimeFormat("en-SG", { dateStyle: "medium", timeStyle: "short" }).format(new Date(record.occurred_at))}</time></td><td data-label="Actor">{actorLabel(record.actor_reference)}</td><td data-label="Role">{actorRole(record)}</td><td data-label="Action"><strong>{titleCase(record.action_type)}</strong></td><td data-label="Target">{titleCase(record.target_table)} · {record.target_id}</td><td data-label="Outcome"><span className={styles.outcome}>{outcome(record)}</span></td></tr>)}</tbody></table></div>
        <aside className={styles.detail} aria-live="polite">{selected ? <><span>Event #{selected.id}</span><h2>{titleCase(selected.action_type)}</h2><dl><div><dt>Recorded</dt><dd>{new Date(selected.occurred_at).toLocaleString("en-SG")}</dd></div><div><dt>Actor</dt><dd>{actorLabel(selected.actor_reference)} · {actorRole(selected)}</dd></div><div><dt>Target</dt><dd>{selected.target_table} · {selected.target_id}</dd></div>{detailRows(selected.details).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl></> : <><span>Event detail</span><h2>Select an event</h2><p>Choose a row to inspect its safe, structured audit evidence.</p></>}</aside>
      </div> : null}

      <nav aria-label="Audit pages" className={styles.pagination}><button disabled={page === 0 || state === "loading"} onClick={() => setPage((value) => Math.max(0, value - 1))} type="button">Previous</button><span>Page {page + 1}</span><button disabled={!hasNext || state === "loading"} onClick={() => setPage((value) => value + 1)} type="button">Next</button></nav>
    </section>
  );
}
