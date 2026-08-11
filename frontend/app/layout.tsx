import "@fontsource/barlow-condensed/500.css";
import "@fontsource/barlow-condensed/600.css";
import "@fontsource/barlow-condensed/700.css";
import "@fontsource/source-sans-3/400.css";
import "@fontsource/source-sans-3/500.css";
import "@fontsource/source-sans-3/600.css";
import type { Metadata } from "next";

import { AppShell } from "@/components/layout/AppShell";
import { AuthProvider } from "@/components/providers/AuthProvider";

import "./globals.css";

export const metadata: Metadata = {
  title: "Epicenter · Clinic readiness",
  description: "A synthetic outpatient administrative-readiness operations demo.",
};

const designContract = `
THESIS: Clinic wayfinding becomes the operating system; refuse the generic card-grid dashboard.
OWN-WORLD: Warm cream fields, surgical green route bands, fixed columns, hairline rules, and room-sign typography.
STORY: Staff see pressure, protect one patient ticket, resolve exceptions, and approve operational action.
FIRST VIEWPORT: A green navigation rail frames a full-width readiness board; the oldest exception and allocation decision stay visible without scrolling.
FORM: Clinical wayfinding board, grounded candidate 3, seed a9c726fc.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, and DESIGN.md`;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <span
          aria-hidden="true"
          className="design-contract"
          dangerouslySetInnerHTML={{ __html: `<!-- ${designContract} -->` }}
        />
        <AuthProvider>
          <AppShell>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}
