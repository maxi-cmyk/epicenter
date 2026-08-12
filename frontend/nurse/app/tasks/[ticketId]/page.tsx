import { TaskWorkspace } from "@/components/tasks/TaskWorkspace";

export default async function TaskPage({ params }: { params: Promise<{ ticketId: string }> }) {
  const { ticketId } = await params;
  return <TaskWorkspace ticketId={ticketId} />;
}
