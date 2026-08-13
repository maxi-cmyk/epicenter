import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(`../${path}`, import.meta.url), "utf8");

test("routes stay split into focused workspaces", () => {
  assert.match(read("nurse/app/page.tsx"), /DashboardView/);
  assert.match(read("nurse/app/review/page.tsx"), /redirect\("\/"\)/);
  assert.match(read("nurse/app/kiosk/page.tsx"), /KioskWorkspace/);
  assert.match(read("patient/app/page.tsx"), /HomeWorkspace/);
  assert.match(read("patient/app/onboarding/page.tsx"), /OnboardingWorkspace/);
  assert.match(read("patient/app/coverage/page.tsx"), /profileEdit/);
  assert.match(read("patient/app/queue/page.tsx"), /QueueWorkspace/);
  assert.throws(() => read("patient/app/review/page.tsx"));
  assert.throws(() => read("patient/app/kiosk/page.tsx"));
  assert.throws(() => read("nurse/app/pre-arrival/page.tsx"));
});

test("the patient dashboard offers official pre-registration without a fixed bottom nav", () => {
  const shell = read("patient/components/layout/PatientShell.tsx");
  const home = read("patient/components/home/HomeWorkspace.tsx");
  assert.doesNotMatch(shell, /Patient destinations|navItems/);
  assert.match(home, /Pre-register for an appointment/);
  assert.match(home, /parkwayshenton\.com\.sg\/make-an-appointment/);
  assert.match(home, /clinic will confirm your/);
});

test("preparation actions edit persisted details and keep queue access contextual", () => {
  const home = read("patient/components/home/HomeWorkspace.tsx");
  const coverage = read("patient/components/coverage/CoverageWorkspace.tsx");
  const questionnairePage = read("patient/app/questionnaire/page.tsx");
  assert.match(home, /aria-label="Edit coverage"/);
  assert.match(home, /aria-label="Edit questionnaire"/);
  assert.match(home, /Check queue/);
  assert.doesNotMatch(home, /Refresh status|Refreshing…/);
  assert.doesNotMatch(home, /href="\/queue">\s*<Ticket/);
  assert.match(coverage, /profileEdit/);
  assert.match(coverage, /submitOnboardingCoverage/);
  assert.match(questionnairePage, /initialEditing=\{params\.edit === "1"\}/);
});

test("the walk-in path preserves one ticket and nurse supervision copy", () => {
  const kiosk = read("nurse/components/kiosk/KioskWorkspace.tsx");
  assert.match(kiosk, /One intake\. One ticket\./);
  assert.match(kiosk, /supervising nurse/i);
  assert.match(kiosk, /must not delay care/i);
});

test("the patient pre-check preserves the registration and identity boundary", () => {
  const preArrival = read("patient/components/prearrival/PreArrivalWorkspace.tsx");
  assert.match(preArrival, /Singpass-authenticated booking/);
  assert.match(preArrival, /Myinfo/);
  assert.match(preArrival, /identity and e-card checks physically on arrival/);
  assert.match(preArrival, /submitPreArrival/);
  assert.match(preArrival, /Submitted for staff confirmation/);
  assert.match(read("patient/lib/api.ts"), /\/patient\/pre-arrival\/submit/);
});

test("questionnaire loading recovers without repeated manual retries", () => {
  const api = read("patient/lib/api.ts");
  const questionnaire = read("patient/components/questionnaire/QuestionnaireWorkspace.tsx");
  assert.match(api, /attempt < 3/);
  assert.match(api, /error\.status === 409/);
  assert.match(api, /error\.status >= 500/);
  assert.match(questionnaire, /The questionnaire could not be loaded automatically/);
  assert.match(questionnaire, /styles\.errorBox/);
});

test("the standard questionnaire keeps its fields while presenting a guided flow", () => {
  const questionnaire = read("patient/components/questionnaire/QuestionnaireWorkspace.tsx");
  const onboarding = read("patient/components/onboarding/OnboardingWorkspace.tsx");
  const upload = read("patient/components/upload/UploadLinkWorkspace.tsx");
  const payment = read("patient/components/payment/PaymentWorkspace.tsx");

  assert.match(questionnaire, /field\.options\?\.map/);
  assert.match(questionnaire, /Section \$\{safeSectionIndex \+ 1\} of/);
  assert.match(questionnaire, /questionnaireProgress/);
  assert.match(questionnaire, /questionnaireTitleLine/);
  assert.match(questionnaire, /General Health<\/span>/);
  assert.match(questionnaire, /Screening Questionnaire<\/span>/);
  assert.match(questionnaire, /Back to home/);
  assert.match(questionnaire, /className=\{styles\.questionnaireBackLink\} href="\/"/);
  assert.ok(questionnaire.indexOf("styles.questionnaireActions") < questionnaire.indexOf("Back to home"));
  assert.match(questionnaire, /styles\.requiredMark/);
  assert.match(questionnaire, /embedded \? styles\.embeddedQuestionnaire/);
  assert.doesNotMatch(questionnaire, /styles\.prefillList/);
  assert.match(questionnaire, /questionnaire\.prefill\.find/);
  assert.match(questionnaire, /aria-label="Questionnaire sections"/);
  assert.match(questionnaire, /sections\.map/);
  assert.match(questionnaire, /void continueTo\(index\)/);
  assert.match(questionnaire, /setViewingSubmittedSection\(true\)/);
  assert.match(questionnaire, /Review answers/);
  assert.doesNotMatch(questionnaire, /Not answered/);
  assert.match(questionnaire, /This questionnaire does not assess medical urgency/);
  assert.match(questionnaire, /Clinical care always takes priority/);
  assert.match(onboarding, /Log in with Singpass/);
  assert.match(onboarding, /active \? null : step\.id/);
  assert.doesNotMatch(onboarding, /Leave and finish later|epicenter:onboarding-paused/);
  assert.match(onboarding, /Return to current step/);
  assert.match(upload, /Contact clinic for a new link/);
  assert.match(upload, /Return to patient sign in/);
  assert.match(payment, /Confirm demo payment/);
  assert.match(payment, /No card is charged and/);
});

test("the dashboard labels all demo data honestly", () => {
  const navigation = read("nurse/components/layout/SideNavigation.tsx");
  const dashboard = read("nurse/components/dashboard/DashboardView.tsx");
  assert.match(navigation, /Clinic readiness/);
  assert.match(dashboard, /Demo data only — confirmations are disabled/);
  assert.doesNotMatch(dashboard, /Clinic API connected/);
  assert.ok(dashboard.indexOf("styles.contextBar") < dashboard.indexOf("{loading ?"));
  assert.match(read("nurse\/lib\/api.ts"), /Reconnect to live clinic data before recording a confirmation/);
});

test("the desktop board elevates exceptions without removing the three visit phases", () => {
  const board = read("nurse/components/dashboard/PatientFlowBoard.tsx");
  const ticket = read("nurse/components/dashboard/TicketRow.tsx");

  assert.match(board, /Incoming/);
  assert.match(board, /Ongoing/);
  assert.match(board, /Finished/);
  assert.doesNotMatch(board, /Open next exception/);
  assert.doesNotMatch(board, /aria-keyshortcuts/);
  assert.match(ticket, /Needs confirmation/);
  assert.match(ticket, /card_finished/);
  assert.doesNotMatch(ticket, />Docs</);
});

test("review exceptions stay contextual and patient-specific", () => {
  const evidence = read("nurse/components/review/EvidencePanel.tsx");
  const gate = read("nurse/components/tasks/ReviewGate.tsx");

  assert.match(evidence, /reviewCase\.evidence_summary/);
  assert.match(evidence, /reviewCase\.next_action/);
  assert.match(evidence, /onConfirm\(\{ method:/);
  assert.doesNotMatch(evidence, /Bluepeak|S••••451A|Executive screening/);
  assert.match(gate, /review_resolved:/);
  assert.match(gate, /"needs_review", reason/);
  assert.doesNotMatch(gate, /"ready", reason/);
});

test("each deployable app validates its own environment", () => {
  assert.match(read("patient/app/layout.tsx"), /validatePatientEnvironment/);
  assert.match(read("nurse/app/layout.tsx"), /validateNurseEnvironment/);
  assert.match(read("patient/.env.example"), /NEXT_PUBLIC_API_BASE_URL/);
  assert.match(read("nurse/.env.example"), /NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY/);
  assert.match(read("patient/lib/env.ts"), /parsed\.protocol !== "http:"/);
  assert.match(read("nurse/lib/env.ts"), /parsed\.protocol !== "http:"/);
});

test("the visual QA auth bypass is development-only", () => {
  const nurseAuth = read("nurse/components/providers/AuthProvider.tsx");
  const patientAuth = read("patient/components/providers/PatientAuthProvider.tsx");
  assert.match(nurseAuth, /NODE_ENV === "development"/);
  assert.match(nurseAuth, /NEXT_PUBLIC_E2E_BYPASS_AUTH/);
  assert.match(patientAuth, /NODE_ENV === "development"/);
  assert.match(patientAuth, /NEXT_PUBLIC_E2E_BYPASS_AUTH/);
  assert.doesNotMatch(read("nurse\/.env.example"), /E2E_BYPASS/);
});

test("patient signup and nurse provisioning stay separate", () => {
  const patientAuth = read("patient/components/providers/PatientAuthProvider.tsx");
  const nurseSignIn = read("nurse/components/providers/StaffSignIn.tsx");
  assert.match(patientAuth, /Create patient account/);
  assert.match(patientAuth, /<SignUp/);
  assert.match(patientAuth, /activatePatientAccount/);
  assert.doesNotMatch(patientAuth, /role selector/i);
  assert.match(nurseSignIn, /withSignUp=\{false\}/);
  assert.match(nurseSignIn, /Self-service sign-up is unavailable/);
  assert.doesNotMatch(nurseSignIn, /<SignUp/);
});

test("staff authorization remains while manual confirmations do not require step-up", () => {
  const provider = read("nurse/components/providers/AuthProvider.tsx");
  const api = read("nurse/lib/api.ts");
  const review = read("nurse/components/tasks/ReviewGate.tsx");
  const packageStep = read("nurse/components/tasks/PackageStep.tsx");
  const kiosk = read("nurse/components/kiosk/KioskWorkspace.tsx");

  assert.match(provider, /fetchStaffSession/);
  assert.match(provider, /Nurse access required/);
  assert.match(api, /reverification-error/);
  assert.match(api, /error\.status === 401 \|\| error\.status === 403/);
  assert.match(review, /await transitionTicket\(/);
  assert.match(packageStep, /await confirmPackage\(/);
  assert.match(kiosk, /await checkInWalkIn\(/);
  assert.doesNotMatch(review, /useReverifiedMutation|useReverification/);
  assert.doesNotMatch(packageStep, /useReverifiedMutation|useReverification/);
  assert.doesNotMatch(kiosk, /useReverifiedMutation|useReverification/);
  assert.doesNotMatch(packageStep, /Demo fallback/);
});

test("the shared workspace contains contracts and presentation primitives only", () => {
  const packageJson = JSON.parse(read("shared/package.json"));
  assert.deepEqual(Object.keys(packageJson.exports).sort(), [
    "./contracts",
    "./contracts/generated",
    "./database",
    "./styles/globals.css",
    "./ui/AuditPanel",
    "./ui/Button",
    "./ui/DatabasePanel",
    "./ui/LoadingBoard",
    "./ui/PageHeader",
    "./ui/StatusBadge",
  ]);
});

test("database is separate from audit and protects only update and delete", () => {
  const database = read("shared/src/ui/DatabasePanel.tsx");
  const nursePage = read("nurse/app/database/page.tsx");
  const pharmacyPage = read("pharmacy/app/database/page.tsx");

  assert.match(read("nurse/components/layout/SideNavigation.tsx"), /Database/);
  assert.match(read("pharmacy/components/layout/SideNavigation.tsx"), /Database/);
  assert.match(nursePage, /createPatient/);
  assert.match(nursePage, /role === "registration" \|\| role === "operations_admin"/);
  assert.match(pharmacyPage, /canManage=\{false\}/);
  assert.match(database, /View/);
  assert.match(database, /Update/);
  assert.match(database, /Delete/);
  assert.match(database, /Enter password to make this change/);
  assert.match(database, /pendingMutation\.kind/);
  assert.doesNotMatch(database, /verifyPassword\(.*create/i);
  assert.doesNotMatch(database, /AuditPanel|fetchAudit/);
  assert.doesNotMatch(database, /Search and maintain approved patient records/);
});

test("audit is a shared read-only surface for nurse and pharmacy", () => {
  const auditPanel = read("shared/src/ui/AuditPanel.tsx");
  assert.match(read("nurse/app/audit/page.tsx"), /AuditPanel/);
  assert.match(read("pharmacy/app/audit/page.tsx"), /AuditPanel/);
  assert.match(read("nurse/components/layout/SideNavigation.tsx"), /Audit trail/);
  assert.match(read("pharmacy/components/layout/SideNavigation.tsx"), /Audit trail/);
  assert.doesNotMatch(auditPanel, /Immutable · read only/);
  assert.match(auditPanel, /Search audit trail/);
  assert.match(auditPanel, /Audit entries cannot be edited or deleted, for viewing purposes only\./);
  assert.doesNotMatch(auditPanel, /editAudit|deleteAudit|updateAudit/);
});
