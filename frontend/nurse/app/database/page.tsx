"use client";

import { useSession } from "@clerk/nextjs";
import { DatabasePanel } from "@epicenter/shared/ui/DatabasePanel";

import { createPatient, deletePatient, fetchPatients, refreshAccessToken, updatePatient } from "@/lib/api";
import { useStaffRole } from "@/components/providers/AuthProvider";

function clerkMessage(reason: unknown) {
  if (reason instanceof Error) return reason.message;
  if (reason && typeof reason === "object" && "errors" in reason) {
    const errors = (reason as { errors?: Array<{ longMessage?: string; message?: string }> }).errors;
    return errors?.[0]?.longMessage || errors?.[0]?.message || "The password could not be verified.";
  }
  return "The password could not be verified.";
}

export default function DatabasePage() {
  const visualQaBypass = process.env.NODE_ENV === "development" && process.env.NEXT_PUBLIC_E2E_BYPASS_AUTH === "true";
  if (visualQaBypass) {
    return <DatabasePanel audience="nurse" canManage createPatient={createPatient} deletePatient={deletePatient} loadPatients={fetchPatients} updatePatient={updatePatient} verifyPassword={async (password) => { if (!password) throw new Error("Enter your password."); }} />;
  }
  return <AuthenticatedDatabase />;
}

function AuthenticatedDatabase() {
  const { session } = useSession();
  const role = useStaffRole();
  const canManage = role === "registration" || role === "operations_admin";
  const verifyPassword = async (password: string) => {
    if (!session) throw new Error("Your staff session is unavailable. Sign in again and retry.");
    try {
      const verification = await session.startVerification({ level: "first_factor" });
      const supportsPassword = verification.supportedFirstFactors?.some((factor) => factor.strategy === "password");
      if (!supportsPassword) throw new Error("This staff account does not have password verification enabled.");
      const result = await session.attemptFirstFactorVerification({ strategy: "password", password });
      if (result.status !== "complete") throw new Error("Additional verification is required before this change can be made.");
      session.clearCache();
      await refreshAccessToken();
    } catch (reason) {
      throw new Error(clerkMessage(reason));
    }
  };
  return <DatabasePanel audience="nurse" canManage={canManage} createPatient={canManage ? createPatient : undefined} deletePatient={canManage ? deletePatient : undefined} loadPatients={fetchPatients} updatePatient={canManage ? updatePatient : undefined} verifyPassword={verifyPassword} />;
}
