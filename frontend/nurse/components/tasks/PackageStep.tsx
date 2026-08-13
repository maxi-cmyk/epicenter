"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { confirmPackage } from "@/lib/api";
import { hasDocuments } from "@/lib/task-steps";
import type { QueueTicket } from "@epicenter/shared/contracts";
import { Button } from "@epicenter/shared/ui/Button";
import { LoadingBoard } from "@epicenter/shared/ui/LoadingBoard";

import { TaskStepShell } from "./TaskStepShell";
import styles from "./Task.module.css";

export function PackageStep({ ticketId }: { ticketId: string }) {
  return (
    <TaskStepShell step="package" ticketId={ticketId}>
      {({ ticket, refresh }) => <PackageStepContent refresh={refresh} ticket={ticket} />}
    </TaskStepShell>
  );
}

function PackageStepContent({ ticket, refresh }: { ticket: QueueTicket; refresh: () => Promise<void> }) {
  const [packageEdit, setPackageEdit] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const packageValue = packageEdit ?? ticket.matched_package ?? "";
  const skip = !hasDocuments(ticket);

  useEffect(() => {
    if (skip) router.replace(`/tasks/${ticket.id}/billing`);
  }, [skip, router, ticket.id]);

  if (skip) return <LoadingBoard />;

  const submit = async () => {
    setPending(true);
    setError("");
    try {
      const trimmed = packageValue.trim();
      const corrected = trimmed !== (ticket.matched_package ?? "").trim() ? trimmed : undefined;
      await confirmPackage(ticket.id, ticket.version, corrected);
      setPackageEdit(null);
      await refresh();
      router.push(`/tasks/${ticket.id}/billing`);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Could not confirm the package.");
    } finally {
      setPending(false);
    }
  };

  return (
    <section aria-labelledby="package-title" className={styles.section}>
      <h2 id="package-title">
        Confirm package
        {ticket.package_confirmed ? <span className={styles.tpaConfirmedBadge}>Confirmed</span> : null}
      </h2>
      <p className={styles.hint}>
        The system checked CHAS + corporate insurance eligibility and matched this patient to a package
        automatically. Recheck it and correct it here if it&apos;s wrong before confirming.
      </p>
      <label className={styles.tpaDocRefLabel}>
        Matched package
        <input onChange={(event) => setPackageEdit(event.target.value)} value={packageValue} />
      </label>
      <Button disabled={pending} onClick={() => void submit()}>
        {pending ? "Confirming…" : ticket.package_confirmed ? "Save & continue" : "Confirm package & continue"}
      </Button>
      {ticket.package_confirmed && ticket.package_confirmed_by ? (
        <p className={styles.hint}>Confirmed by {ticket.package_confirmed_by}</p>
      ) : null}
      {error ? <p className={styles.error}>{error}</p> : null}
    </section>
  );
}
