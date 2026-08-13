"use client";

import Link from "next/link";

import { usePharmacyQueue } from "@/hooks/usePharmacyQueue";
import { LoadingBoard } from "@epicenter/shared/ui/LoadingBoard";

import styles from "./Pharmacy.module.css";

export function PharmacyQueueBoard() {
  const { tickets, loading } = usePharmacyQueue();

  if (loading || !tickets) return <LoadingBoard />;

  return (
    <section className={styles.queuePage}>
      <header className={styles.queueHeader}>
        <h1>Pharmacy queue</h1>
      </header>
      {tickets.length === 0 ? (
        <p className={styles.queueEmpty}>No patients in consultation or finished yet.</p>
      ) : (
        <div className={styles.queueGrid}>
          {tickets.map((ticket) => (
            <Link className={styles.queueCard} href={`/tickets/${ticket.id}`} key={ticket.id}>
              <div className={styles.queueCardHead}>
                <span className={styles.queueCardId}>{ticket.id}</span>
                {ticket.documents.length > 0 ? <span className={styles.queueCardBadge}>Docs</span> : null}
              </div>
              <h2 className={styles.queueCardName}>{ticket.patient_name}</h2>
              <p className={styles.queueCardMeta}>
                {ticket.processing_stage} · {ticket.actual_room ?? "Room not assigned"}
              </p>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
