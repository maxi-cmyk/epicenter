"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchPharmacyQueue } from "@/lib/api";
import type { QueueTicket } from "@epicenter/shared/contracts";

export function usePharmacyQueue() {
  const [tickets, setTickets] = useState<QueueTicket[] | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    setTickets(await fetchPharmacyQueue());
    setLoading(false);
  }, []);

  useEffect(() => {
    let active = true;
    void fetchPharmacyQueue().then((result) => {
      if (!active) return;
      setTickets(result);
      setLoading(false);
    });
    return () => {
      active = false;
    };
  }, []);

  return { tickets, loading, refresh };
}
