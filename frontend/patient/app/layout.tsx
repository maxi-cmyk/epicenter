import "@fontsource/barlow-condensed/500.css";
import "@fontsource/barlow-condensed/600.css";
import "@fontsource/barlow-condensed/700.css";
import "@fontsource/source-sans-3/400.css";
import "@fontsource/source-sans-3/500.css";
import "@fontsource/source-sans-3/600.css";
import "@epicenter/shared/styles/globals.css";
import type { Metadata } from "next";

import { PatientShell } from "@/components/layout/PatientShell";
import { PatientAuthProvider } from "@/components/providers/PatientAuthProvider";
import { validatePatientEnvironment } from "@/lib/env";

export const metadata: Metadata = {
  title: "Epicenter · Patient registration",
  description: "Synthetic pre-arrival registration and coverage pre-check.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  validatePatientEnvironment();

  return (
    <html lang="en">
      <body>
        <PatientAuthProvider>
          <PatientShell>{children}</PatientShell>
        </PatientAuthProvider>
      </body>
    </html>
  );
}
