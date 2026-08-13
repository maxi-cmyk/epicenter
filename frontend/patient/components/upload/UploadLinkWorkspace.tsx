"use client";

import { AlertCircle, ExternalLink, RotateCcw } from "lucide-react";
import Link from "next/link";
import { useCallback, useState } from "react";
import { useParams } from "next/navigation";

import { Button } from "@epicenter/shared/ui/Button";
import type { UploadLinkSession } from "@epicenter/shared/contracts";

import { CoverageWorkspace } from "@/components/coverage/CoverageWorkspace";
import { resolveUploadLink } from "@/lib/api";
import { useMountedLoad } from "@/lib/useMountedLoad";

import styles from "@/components/home/Journey.module.css";

const CLINIC_DETAILS_URL =
  "https://www.parkwayshenton.com.sg/find-a-clinic/detail/parkway-shenton-medical-clinic-harbourfront";

function LinkRecovery({ description, onRetry, title }: { description: string; onRetry: () => void; title: string }) {
  return (
    <div className={styles.recoveryPage} role="alert">
      <section className={styles.recoveryPanel}>
        <AlertCircle aria-hidden="true" size={30} />
        <div>
          <h1>{title}</h1>
          <p>{description}</p>
          <small>Trying again will not remove documents you previously submitted.</small>
        </div>
        <div className={styles.recoveryActions}>
          <Button icon={<RotateCcw aria-hidden="true" size={17} />} onClick={onRetry} variant="secondary">
            Try this link again
          </Button>
          <a href={CLINIC_DETAILS_URL} rel="noreferrer" target="_blank">
            Contact clinic for a new link <ExternalLink aria-hidden="true" size={16} />
          </a>
          <Link href="/sign-in">Return to patient sign in</Link>
        </div>
      </section>
    </div>
  );
}

export function UploadLinkWorkspace() {
  const params = useParams<{ token: string }>();
  const token = params.token;
  const [session, setSession] = useState<UploadLinkSession | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setSession(await resolveUploadLink(token));
      setError(null);
    } catch (loadError: unknown) {
      setError(loadError instanceof Error ? loadError.message : "This upload link could not be opened.");
    }
  }, [token]);

  useMountedLoad(load);

  if (error) {
    return (
      <LinkRecovery
        description="We could not verify this upload link. It may have expired, already been used, or temporarily be unavailable."
        onRetry={() => void load()}
        title="Upload link unavailable"
      />
    );
  }

  if (!session) {
    return (
      <div aria-busy="true" className={styles.page}>
        <div className={styles.skeletonCard} />
      </div>
    );
  }

  if (!session.valid) {
    return (
      <LinkRecovery description={session.next_action} onRetry={() => void load()} title={session.message} />
    );
  }

  return (
    <div className={styles.page}>
      <p className={styles.muted}>{session.message}</p>
      <CoverageWorkspace />
    </div>
  );
}
