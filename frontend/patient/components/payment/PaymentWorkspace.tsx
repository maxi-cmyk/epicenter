"use client";

import { Beaker } from "lucide-react";
import { useCallback, useState } from "react";
import { useMountedLoad } from "@/lib/useMountedLoad";

import { Button } from "@epicenter/shared/ui/Button";
import { PageHeader } from "@epicenter/shared/ui/PageHeader";
import type { PatientPaymentSummary } from "@epicenter/shared/contracts";

import { getPatientPayment, submitMockPayment } from "@/lib/api";

import styles from "../home/Journey.module.css";

export function PaymentWorkspace() {
  const [payment, setPayment] = useState<PatientPaymentSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setPayment(await getPatientPayment());
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load payment.");
    } finally {
      setLoading(false);
    }
  }, []);

  useMountedLoad(load);

  async function pay() {
    if (!payment?.appointment_id) return;
    setSubmitting(true);
    setError(null);
    try {
      setPayment(
        await submitMockPayment({
          appointment_id: payment.appointment_id,
          expected_version: payment.version,
          idempotency_key: crypto.randomUUID(),
        }),
      );
    } catch (payError) {
      setError(payError instanceof Error ? payError.message : "Demo payment failed.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading && !payment) {
    return (
      <div aria-busy="true" className={styles.page}>
        <div className={styles.skeletonCard} />
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <PageHeader
        description="Payment is available only after an appointment is booked and billing is ready."
        title="Payment summary"
      />
      {payment ? (
        <section className={styles.panel}>
          {!payment.appointment_id ? (
            <p>No appointment has been made. You can return here after the clinic books your visit.</p>
          ) : (
            <>
          <span className={styles.mockedTag}>
            <Beaker aria-hidden="true" size={14} /> Mocked payment
          </span>
          <dl className={styles.summaryList}>
            <div>
              <dt>Package</dt>
              <dd>{payment.package_label}</dd>
            </div>
            <div>
              <dt>Covered</dt>
              <dd>{payment.amount_covered}</dd>
            </div>
            <div>
              <dt>You pay</dt>
              <dd>{payment.amount_patient_payable}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>{payment.status_detail}</dd>
            </div>
            {payment.receipt_reference ? (
              <div>
                <dt>Receipt</dt>
                <dd>{payment.receipt_reference}</dd>
              </div>
            ) : null}
          </dl>

          {payment.status === "mocked_paid" ? (
            <div className={styles.successBox} role="status">
              <strong>Demo payment recorded</strong>
              <span>This receipt is synthetic and does not move money.</span>
            </div>
          ) : (
            <Button
              disabled={submitting || payment.status === "not_ready" || payment.status === "mock_processing"}
              onClick={() => void pay()}
            >
              {submitting ? "Processing…" : payment.status === "mock_failed" ? "Retry demo payment" : "Pay now — demo"}
            </Button>
          )}
            </>
          )}

          {error ? (
            <div className={styles.errorBox} role="alert">
              {error}
            </div>
          ) : null}
        </section>
      ) : (
        <div className={styles.errorBox} role="alert">
          {error ?? "Payment unavailable"}
          <Button onClick={() => void load()}>Retry</Button>
        </div>
      )}
    </div>
  );
}
