"use client";

import { useCallback, useState } from "react";
import { useParams } from "next/navigation";

import { PageHeader } from "@epicenter/shared/ui/PageHeader";
import type { UploadLinkSession } from "@epicenter/shared/contracts";

import { CoverageWorkspace } from "@/components/coverage/CoverageWorkspace";
import { resolveUploadLink } from "@/lib/api";
import { useMountedLoad } from "@/lib/useMountedLoad";

import styles from "@/components/home/Journey.module.css";

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
      <div className={styles.page} role="alert">
        <PageHeader description={error} title="Upload link unavailable" />
      </div>
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
      <div className={styles.page}>
        <PageHeader description={session.next_action} title={session.message} />
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <p className={styles.muted}>{session.message}</p>
      <CoverageWorkspace />
    </div>
  );
}
