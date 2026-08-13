import { FormsGuidanceStep } from "@/components/tasks/FormsGuidanceStep";

export default async function FormsStepPage({ params }: { params: Promise<{ ticketId: string }> }) {
  const { ticketId } = await params;
  return <FormsGuidanceStep ticketId={ticketId} />;
}
