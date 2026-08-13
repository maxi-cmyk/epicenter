import { PackageStep } from "@/components/tasks/PackageStep";

export default async function PackageStepPage({ params }: { params: Promise<{ ticketId: string }> }) {
  const { ticketId } = await params;
  return <PackageStep ticketId={ticketId} />;
}
