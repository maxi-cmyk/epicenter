"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchDashboard } from "@/lib/api";
import type { DashboardSnapshot } from "@epicenter/shared/contracts";

export function useDashboard() {
  const [data, setData] = useState<DashboardSnapshot | null>(null);
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Deliberately does not toggle `loading` — that flag gates a full-page LoadingBoard
  // swap in consumers, which would unmount tall content mid-refresh and snap the
  // scroll position back to the top (e.g. right after confirming a document).
  const refresh = useCallback(async () => {
    setRefreshing(true);
    const result = await fetchDashboard();
    setData(result.data);
    setSource(result.source);
    setRefreshing(false);
  }, []);

  useEffect(() => {
    let active = true;
    void fetchDashboard().then((result) => {
      if (!active) return;
      setData(result.data);
      setSource(result.source);
      setLoading(false);
    });
    return () => {
      active = false;
    };
  }, []);

  return { data, source, loading, refreshing, refresh };
}
