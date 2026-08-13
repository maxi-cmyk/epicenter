"use client";

import { fetchAudit } from "@/lib/api";
import { AuditPanel } from "@epicenter/shared/ui/AuditPanel";

export default function AuditPage() {
  return <AuditPanel loadAudit={fetchAudit} />;
}
