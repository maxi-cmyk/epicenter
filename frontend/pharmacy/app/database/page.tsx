"use client";

import { DatabasePanel } from "@epicenter/shared/ui/DatabasePanel";

import { fetchPatients } from "@/lib/api";

export default function DatabasePage() {
  return <DatabasePanel audience="pharmacy" canManage={false} loadPatients={fetchPatients} verifyPassword={async () => undefined} />;
}
