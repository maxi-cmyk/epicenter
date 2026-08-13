import { BillingStep } from "@/components/tasks/BillingStep";

export default async function BillingStepPage({ params }: { params: Promise<{ ticketId: string }> }) {
  const { ticketId } = await params;
  return <BillingStep ticketId={ticketId} />;
}
