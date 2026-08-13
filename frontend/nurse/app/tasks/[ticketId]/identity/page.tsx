import { IdentityStep } from "@/components/tasks/IdentityStep";

export default async function IdentityStepPage({ params }: { params: Promise<{ ticketId: string }> }) {
  const { ticketId } = await params;
  return <IdentityStep ticketId={ticketId} />;
}
