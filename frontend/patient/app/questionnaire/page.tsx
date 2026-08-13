import { QuestionnaireWorkspace } from "@/components/questionnaire/QuestionnaireWorkspace";

type QuestionnairePageProps = {
  searchParams: Promise<{
    appointment_id?: string;
    edit?: string;
  }>;
};

export default async function QuestionnairePage({ searchParams }: QuestionnairePageProps) {
  const params = await searchParams;
  return (
    <QuestionnaireWorkspace
      appointmentId={params.appointment_id}
      initialEditing={params.edit === "1"}
    />
  );
}
