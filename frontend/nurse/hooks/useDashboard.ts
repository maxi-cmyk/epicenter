"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchDashboard } from "@/lib/api";
import type { DashboardSnapshot } from "@epicenter/shared/contracts";

export function useDashboard() {
  const [data, setData] = useState<DashboardSnapshot | null>(null);
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Deliberately does not toggle `loading` — that flag gates a full-page LoadingBoard
  // swap in consumers, which would unmount tall content mid-refresh and snap the
  // scroll position back to the top (e.g. right after confirming a document).
  const refresh = useCallback(async () => {
    setRefreshing(true);
    setError("");
    try {
      const result = await fetchDashboard();
      setData(result.data);
      setSource(result.source);
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Clinic data could not be refreshed.");
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    void fetchDashboard()
      .then((result) => {
        if (!active) return;
        setData(result.data);
        setSource(result.source);
      })
      .catch((loadError: unknown) => {
        if (!active) return;
        setError(loadError instanceof Error ? loadError.message : "Clinic data could not be loaded.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  return { data, error, source, loading, refreshing, refresh };
}
