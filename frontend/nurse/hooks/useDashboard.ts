"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchDashboard } from "@/lib/api";
import type { DashboardSnapshot } from "@epicenter/shared/contracts";

export function useDashboard() {
  const [data, setData] = useState<DashboardSnapshot | null>(null);
  const [source, setSource] = useState<"api" | "fallback">("fallback");
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    const result = await fetchDashboard();
    setData(result.data);
    setSource(result.source);
    setLoading(false);
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

  return { data, source, loading, refresh };
}
