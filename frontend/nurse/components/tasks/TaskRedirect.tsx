"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useDashboard } from "@/hooks/useDashboard";
import { nextIncompleteStep } from "@/lib/task-steps";
import { LoadingBoard } from "@epicenter/shared/ui/LoadingBoard";

export function TaskRedirect({ ticketId }: { ticketId: string }) {
  const { data, loading } = useDashboard();
  const router = useRouter();

  useEffect(() => {
    if (loading || !data) return;
    const ticket = data.tickets.find((item) => item.id === ticketId);
    router.replace(ticket ? `/tasks/${ticketId}/${nextIncompleteStep(ticket)}` : "/");
  }, [data, loading, ticketId, router]);

  return <LoadingBoard />;
}
