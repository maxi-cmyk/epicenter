import "@fontsource/barlow-condensed/500.css";
import "@fontsource/barlow-condensed/600.css";
import "@fontsource/barlow-condensed/700.css";
import "@fontsource/source-sans-3/400.css";
import "@fontsource/source-sans-3/500.css";
import "@fontsource/source-sans-3/600.css";
import "@epicenter/shared/styles/globals.css";
import type { Metadata } from "next";

import { AppShell } from "@/components/layout/AppShell";
import { AuthProvider } from "@/components/providers/AuthProvider";
import { validatePharmacyEnvironment } from "@/lib/env";

export const metadata: Metadata = {
  title: "Epicenter · Pharmacy panel",
  description: "Synthetic clinic medication dispensing and TPA submission workspace.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  validatePharmacyEnvironment();

  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <AppShell>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}
