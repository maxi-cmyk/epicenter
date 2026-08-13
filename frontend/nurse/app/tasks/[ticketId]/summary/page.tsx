import { SummaryStep } from "@/components/tasks/SummaryStep";

export default async function SummaryStepPage({ params }: { params: Promise<{ ticketId: string }> }) {
  const { ticketId } = await params;
  return <SummaryStep ticketId={ticketId} />;
}
