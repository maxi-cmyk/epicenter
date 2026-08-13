import { TaskRedirect } from "@/components/tasks/TaskRedirect";

export default async function TaskPage({ params }: { params: Promise<{ ticketId: string }> }) {
  const { ticketId } = await params;
  return <TaskRedirect ticketId={ticketId} />;
}
