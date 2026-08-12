import { PharmacyWorkspace } from "@/components/pharmacy/PharmacyWorkspace";

export default async function TicketPage({ params }: { params: Promise<{ ticketId: string }> }) {
  const { ticketId } = await params;
  return <PharmacyWorkspace ticketId={ticketId} />;
}
