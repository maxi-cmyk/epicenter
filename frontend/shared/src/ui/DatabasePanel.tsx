"use client";

import type {
  PatientCreateRequest,
  PatientDeleteRequest,
  PatientList,
  PatientRecord,
  PatientUpdateRequest,
} from "../contracts";
import {
  ChevronLeft,
  ChevronRight,
  Eye,
  MoreHorizontal,
  Pencil,
  Plus,
  Search,
  Trash2,
  X,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { PageHeader } from "./PageHeader";
import styles from "./DatabasePanel.module.css";

type LoadPatients = (query: { search?: string; contactFilter?: string; sort?: string; offset: number; limit: number }) => Promise<PatientList>;
type CreatePatient = (request: PatientCreateRequest) => Promise<PatientRecord>;
type UpdatePatient = (patientId: number, request: PatientUpdateRequest) => Promise<PatientRecord>;
type DeletePatient = (patientId: number, request: PatientDeleteRequest) => Promise<PatientRecord>;

type Props = {
  canManage: boolean;
  loadPatients: LoadPatients;
  createPatient?: CreatePatient;
  updatePatient?: UpdatePatient;
  deletePatient?: DeletePatient;
  verifyPassword: (password: string) => Promise<void>;
};

type DetailMode = "view" | "create" | "update" | "delete";
type PendingMutation =
  | { kind: "update"; record: PatientRecord }
  | { kind: "delete"; record: PatientRecord };

const PAGE_SIZE = 20;

function displayDate(value?: string | null) {
  if (!value) return "Not recorded";
  return new Intl.DateTimeFormat("en-SG", { dateStyle: "medium" }).format(new Date(`${value}T00:00:00`));
}

async function sha256(value: string) {
  const bytes = new TextEncoder().encode(value.trim().toUpperCase());
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function maskIdentifier(value: string) {
  const cleaned = value.trim().toUpperCase();
  return `${"*".repeat(Math.max(4, cleaned.length - 4))}${cleaned.slice(-4)}`;
}

export function DatabasePanel({
  canManage,
  loadPatients,
  createPatient,
  updatePatient,
  deletePatient,
  verifyPassword,
}: Props) {
  const [search, setSearch] = useState("");
  const [contactFilter, setContactFilter] = useState("all");
  const [sort, setSort] = useState("name");
  const [page, setPage] = useState(0);
  const [records, setRecords] = useState<PatientRecord[]>([]);
  const [selected, setSelected] = useState<PatientRecord | null>(null);
  const [menuId, setMenuId] = useState<number | null>(null);
  const [detailMode, setDetailMode] = useState<DetailMode>("view");
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [reload, setReload] = useState(0);
  const [pendingMutation, setPendingMutation] = useState<PendingMutation | null>(null);

  const query = useMemo(
    () => ({ search: search.trim() || undefined, contactFilter, sort, offset: page * PAGE_SIZE, limit: PAGE_SIZE + 1 }),
    [contactFilter, page, search, sort],
  );

  useEffect(() => {
    let active = true;
    const timer = window.setTimeout(() => {
      setState("loading");
      setError("");
      void loadPatients(query)
        .then((result) => {
          if (!active) return;
          setRecords(result.records);
          setSelected((current) => result.records.find((record) => record.id === current?.id) ?? null);
          setState("ready");
        })
        .catch((reason: unknown) => {
          if (!active) return;
          setRecords([]);
          setSelected(null);
          setError(reason instanceof Error ? reason.message : "The database could not be loaded.");
          setState("error");
        });
    }, 220);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [loadPatients, query, reload]);

  const hasNext = records.length > PAGE_SIZE;
  const visibleRecords = records.slice(0, PAGE_SIZE);

  const chooseAction = (record: PatientRecord, mode: DetailMode) => {
    setSelected(record);
    if (mode === "update" || mode === "delete") setPendingMutation({ kind: mode, record });
    else setDetailMode(mode);
    setMenuId(null);
    setError("");
    setNotice("");
  };

  const completeMutation = async (request: PatientUpdateRequest | PatientDeleteRequest) => {
    if (!pendingMutation) return;
    try {
      if (pendingMutation.kind === "update") {
        if (!updatePatient) throw new Error("Patient updates are unavailable for this account.");
        const updated = await updatePatient(pendingMutation.record.id, request as PatientUpdateRequest);
        setSelected(updated);
        setNotice(`${updated.full_name} was updated.`);
      } else {
        if (!deletePatient) throw new Error("Patient deletion is unavailable for this account.");
        await deletePatient(pendingMutation.record.id, request as PatientDeleteRequest);
        setSelected(null);
        setNotice(`${pendingMutation.record.full_name} was archived.`);
      }
      setDetailMode("view");
      setReload((value) => value + 1);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The change could not be completed.");
    } finally {
      setPendingMutation(null);
    }
  };

  return (
    <section className={styles.workspace}>
      <PageHeader
        actions={
          canManage && createPatient ? (
            <button className={styles.createButton} onClick={() => { setSelected(null); setDetailMode("create"); }} type="button">
              <Plus aria-hidden="true" size={18} /> Add patient
            </button>
          ) : undefined
        }
        title="Database"
      />

      <div className={styles.controls}>
        <label className={styles.searchBox}>
          <Search aria-hidden="true" size={20} />
          <span className="sr-only">Search patient database</span>
          <input
            onChange={(event) => { setSearch(event.target.value); setPage(0); }}
            placeholder="Search patient name"
            type="search"
            value={search}
          />
          {search ? <button aria-label="Clear search" onClick={() => setSearch("")} type="button"><X size={17} /></button> : null}
        </label>
        <div className={styles.filters}>
          <label>Contact details<select onChange={(event) => { setContactFilter(event.target.value); setPage(0); }} value={contactFilter}><option value="all">All records</option><option value="email">Has email</option><option value="mobile">Has mobile</option><option value="complete">Email and mobile</option></select></label>
          <label>Sort by<select onChange={(event) => { setSort(event.target.value); setPage(0); }} value={sort}><option value="name">Patient name</option><option value="reference">Patient reference</option><option value="dob">Date of birth</option></select></label>
        </div>
      </div>

      {notice ? <div className={styles.notice} role="status">{notice}</div> : null}
      {error && state !== "error" ? <div className={styles.inlineError} role="alert">{error}</div> : null}
      {state === "error" ? <div className={styles.message} role="alert"><strong>Database unavailable</strong><p>{error}</p><button onClick={() => setReload((value) => value + 1)} type="button">Try again</button></div> : null}
      {state === "loading" ? <div className={styles.loading} role="status">Loading clinic records…</div> : null}
      {state === "ready" && visibleRecords.length === 0 ? <div className={styles.message}><strong>No patient records found</strong><p>Adjust the search or contact filter.</p></div> : null}

      {state === "ready" && visibleRecords.length ? (
        <div className={styles.databaseLayout}>
          <div className={styles.tableWrap}>
            <table>
              <thead><tr><th>Patient</th><th>Reference</th><th>Date of birth</th><th>Contact</th><th><span className="sr-only">Actions</span></th></tr></thead>
              <tbody>
                {visibleRecords.map((record) => (
                  <tr
                    aria-selected={menuId === record.id || selected?.id === record.id}
                    key={record.id}
                    onClick={() => setMenuId((current) => current === record.id ? null : record.id)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        setMenuId((current) => current === record.id ? null : record.id);
                      }
                    }}
                    tabIndex={0}
                  >
                    <td data-label="Patient"><strong>{record.full_name}</strong><small>{record.identifier_masked}</small></td>
                    <td data-label="Reference">{record.source_record_key}</td>
                    <td data-label="Date of birth">{displayDate(record.date_of_birth)}</td>
                    <td data-label="Contact"><span>{record.contact_mobile || "No mobile"}</span><small>{record.email || "No email"}</small></td>
                    <td className={styles.actionCell} data-label="Actions">
                      <button aria-expanded={menuId === record.id} aria-label={`Actions for ${record.full_name}`} className={styles.moreButton} onClick={(event) => { event.stopPropagation(); setMenuId((current) => current === record.id ? null : record.id); }} type="button"><MoreHorizontal aria-hidden="true" size={20} /></button>
                      {menuId === record.id ? (
                        <div className={styles.rowMenu} onClick={(event) => event.stopPropagation()} role="menu">
                          <button onClick={() => chooseAction(record, "view")} role="menuitem" type="button"><Eye aria-hidden="true" size={16} />View</button>
                          {canManage ? <button onClick={() => chooseAction(record, "update")} role="menuitem" type="button"><Pencil aria-hidden="true" size={16} />Update</button> : null}
                          {canManage ? <button className={styles.deleteAction} onClick={() => chooseAction(record, "delete")} role="menuitem" type="button"><Trash2 aria-hidden="true" size={16} />Delete</button> : null}
                        </div>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <aside className={styles.detailPanel} aria-live="polite">
            {detailMode === "create" && createPatient ? <CreatePatientForm createPatient={createPatient} onCreated={(record) => { setSelected(record); setDetailMode("view"); setNotice(`${record.full_name} was added.`); setReload((value) => value + 1); }} onError={setError} /> : null}
            {detailMode === "view" ? <PatientDetail canManage={canManage} record={selected} /> : null}
          </aside>
        </div>
      ) : null}

      <nav aria-label="Database pages" className={styles.pagination}>
        <button disabled={page === 0 || state === "loading"} onClick={() => setPage((value) => Math.max(0, value - 1))} type="button"><ChevronLeft size={17} />Previous</button>
        <span>Page {page + 1}</span>
        <button disabled={!hasNext || state === "loading"} onClick={() => setPage((value) => value + 1)} type="button">Next<ChevronRight size={17} /></button>
      </nav>

      {pendingMutation ? (
        <PasswordConfirmationModal
          action={pendingMutation.kind}
          onCancel={() => setPendingMutation(null)}
          onConfirmed={completeMutation}
          record={pendingMutation.record}
          verifyPassword={verifyPassword}
        />
      ) : null}
    </section>
  );
}

function PatientDetail({ record, canManage }: { record: PatientRecord | null; canManage: boolean }) {
  if (!record) return <div className={styles.emptyDetail}><Eye aria-hidden="true" size={26} /><h2>Select a patient</h2><p>{canManage ? "Click a row and choose View, Update, or Delete." : "Click a row and choose View to inspect its approved fields."}</p></div>;
  return <><span>Patient record</span><h2>{record.full_name}</h2><dl><div><dt>Patient reference</dt><dd>{record.source_record_key}</dd></div><div><dt>Identifier</dt><dd>{record.identifier_masked}</dd></div><div><dt>Date of birth</dt><dd>{displayDate(record.date_of_birth)}</dd></div><div><dt>Mobile</dt><dd>{record.contact_mobile || "Not recorded"}</dd></div><div><dt>Email</dt><dd>{record.email || "Not recorded"}</dd></div><div><dt>Record version</dt><dd>{record.version}</dd></div></dl></>;
}

function CreatePatientForm({ createPatient, onCreated, onError }: { createPatient: CreatePatient; onCreated: (record: PatientRecord) => void; onError: (message: string) => void }) {
  const [submitting, setSubmitting] = useState(false);
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setSubmitting(true); onError("");
    const form = new FormData(event.currentTarget);
    try {
      const identifier = String(form.get("identifier") || "");
      const record = await createPatient({
        source_record_key: `manual:${crypto.randomUUID()}`,
        identifier_hash: await sha256(identifier), identifier_masked: maskIdentifier(identifier),
        full_name: String(form.get("fullName") || ""), date_of_birth: String(form.get("dateOfBirth") || "") || null,
        email: String(form.get("email") || "") || null, contact_mobile: String(form.get("mobile") || "") || null,
        reason: String(form.get("reason") || ""), idempotency_key: crypto.randomUUID(),
      });
      onCreated(record);
    } catch (reason) { onError(reason instanceof Error ? reason.message : "The patient could not be added."); }
    finally { setSubmitting(false); }
  };
  return <form className={styles.recordForm} onSubmit={submit}><span>New record</span><h2>Add patient</h2><label>Full name<input name="fullName" required /></label><label>NRIC / FIN / passport<input autoComplete="off" minLength={4} name="identifier" required /><small>Used only to create a one-way hash and masked identifier.</small></label><label>Date of birth<input name="dateOfBirth" type="date" /></label><label>Mobile<input name="mobile" /></label><label>Email<input name="email" type="email" /></label><label>Reason<textarea name="reason" required rows={3} /></label><button disabled={submitting} type="submit">{submitting ? "Adding patient…" : "Add patient"}</button></form>;
}

function PasswordConfirmationModal({ action, record, verifyPassword, onCancel, onConfirmed }: { action: "update" | "delete"; record: PatientRecord; verifyPassword: (password: string) => Promise<void>; onCancel: () => void; onConfirmed: (request: PatientUpdateRequest | PatientDeleteRequest) => Promise<void> }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLElement>(null);
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  useEffect(() => {
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    inputRef.current?.focus();
    return () => previousFocus?.focus();
  }, []);
  useEffect(() => {
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !submitting) onCancel();
      if (event.key !== "Tab") return;
      const focusable = Array.from(dialogRef.current?.querySelectorAll<HTMLElement>("button:not([disabled]), input:not([disabled]), textarea:not([disabled])") ?? []);
      if (!focusable.length) return;
      const first = focusable[0]; const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onCancel, submitting]);
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setSubmitting(true); setError("");
    try {
      const form = new FormData(event.currentTarget);
      const reason = String(form.get("reason") || "");
      const request = action === "update"
        ? { expected_version: record.version, full_name: String(form.get("fullName") || ""), email: String(form.get("email") || "") || null, contact_mobile: String(form.get("mobile") || "") || null, reason, idempotency_key: crypto.randomUUID() }
        : { expected_version: record.version, reason, idempotency_key: crypto.randomUUID() };
      await verifyPassword(password); setPassword(""); await onConfirmed(request);
    }
    catch (reason) { setPassword(""); setError(reason instanceof Error ? reason.message : "The password could not be verified."); inputRef.current?.focus(); }
    finally { setSubmitting(false); }
  };
  return <div className={styles.modalBackdrop} onMouseDown={(event) => { if (event.target === event.currentTarget && !submitting) onCancel(); }}><section aria-describedby="password-modal-description" aria-labelledby="password-modal-title" aria-modal="true" className={styles.passwordModal} ref={dialogRef} role="dialog"><span>{action === "delete" ? "Confirm deletion" : "Confirm update"}</span><h2 id="password-modal-title">Enter password to make this change</h2><p id="password-modal-description">{action === "delete" ? "Archive" : "Update"} <strong>{record.full_name}</strong>. Password verification is required to commit.</p><form onSubmit={submit}>{action === "update" ? <div className={styles.modalFields}><label>Full name<input defaultValue={record.full_name} name="fullName" required /></label><label>Mobile<input defaultValue={record.contact_mobile ?? ""} name="mobile" /></label><label>Email<input defaultValue={record.email ?? ""} name="email" type="email" /></label></div> : <p className={styles.deleteSummary}>The patient will be removed from active searches but retained for recovery and audit history.</p>}<label>{action === "delete" ? "Reason for deletion" : "Reason for change"}<textarea name="reason" required rows={3} /></label><label>Password<input autoComplete="current-password" onChange={(event) => setPassword(event.target.value)} ref={inputRef} required type="password" value={password} /></label>{error ? <p className={styles.modalError} role="alert">{error}</p> : null}<div className={styles.formActions}><button className={styles.cancelButton} disabled={submitting} onClick={onCancel} type="button">Cancel</button><button className={action === "delete" ? styles.dangerButton : undefined} disabled={submitting || !password} type="submit">{submitting ? "Verifying…" : action === "delete" ? "Confirm deletion" : "Confirm update"}</button></div></form></section></div>;
}
