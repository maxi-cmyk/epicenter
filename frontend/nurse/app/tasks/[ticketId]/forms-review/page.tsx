import { FormsReviewStep } from "@/components/tasks/FormsReviewStep";

export default async function FormsReviewStepPage({ params }: { params: Promise<{ ticketId: string }> }) {
  const { ticketId } = await params;
  return <FormsReviewStep ticketId={ticketId} />;
}
