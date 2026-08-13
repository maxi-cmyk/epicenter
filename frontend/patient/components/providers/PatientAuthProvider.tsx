"use client";

import { ClerkLoaded, ClerkLoading, ClerkProvider, Show, SignIn, SignUp, UserButton, useAuth } from "@clerk/nextjs";
import { ShieldCheck } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@epicenter/shared/ui/Button";

import { activatePatientAccount, setAccessTokenProvider } from "@/lib/api";

import styles from "./PatientAuthProvider.module.css";

type PatientAuthProviderProps = {
  children: React.ReactNode;
};

export function PatientAuthProvider({ children }: PatientAuthProviderProps) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  const visualQaBypass =
    process.env.NODE_ENV === "development" && process.env.NEXT_PUBLIC_E2E_BYPASS_AUTH === "true";
  const pathname = usePathname();
  const uploadLinkRoute = pathname?.startsWith("/upload/");

  if (visualQaBypass || uploadLinkRoute) return children;
  if (!publishableKey) {
    return (
      <main className={styles.configurationError}>
        <span>Configuration required</span>
        <h1>Patient authentication is unavailable</h1>
        <p>Add the Clerk publishable key to the patient frontend environment.</p>
      </main>
    );
  }

  return (
    <ClerkProvider
      appearance={{
        elements: {
          footerAction: { display: "none" },
          formButtonPrimary: { minHeight: "44px" },
          formFieldInput: { minHeight: "44px" },
          socialButtonsBlockButton: { minHeight: "44px" },
        },
        variables: {
          colorPrimary: "#17473a",
          colorBackground: "#fffdf5",
          borderRadius: "8px",
          fontFamily: '"Source Sans 3", sans-serif',
        },
      }}
      publishableKey={publishableKey}
    >
      <ClerkLoading>
        <div aria-live="polite" className={styles.loading}>Establishing secure patient access…</div>
      </ClerkLoading>
      <ClerkLoaded>
        <Show when="signed-out"><PatientAccess initialMode={pathname === "/sign-in" ? "sign-in" : "sign-up"} /></Show>
        <Show when="signed-in"><PatientSession>{children}</PatientSession></Show>
      </ClerkLoaded>
    </ClerkProvider>
  );
}

function PatientAccess({ initialMode }: { initialMode: "sign-up" | "sign-in" }) {
  const [mode, setMode] = useState<"sign-up" | "sign-in">(initialMode);

  return (
    <main className={styles.accessPage}>
      <section className={styles.context}>
        <div className={styles.brand}><span aria-hidden="true">E</span><strong>Epicenter</strong></div>
        <div>
          <h1>Prepare before your clinic visit</h1>
          <p>Create a patient account to open onboarding for your first visit. Staff access is provisioned separately and cannot be selected here.</p>
        </div>
        <small><ShieldCheck aria-hidden="true" size={16} /> Synthetic demonstration · no live patient data</small>
      </section>
      <section aria-label="Patient account access" className={styles.control}>
        <div className={styles.task}>
          <div className={styles.modeSwitch}>
            <button aria-pressed={mode === "sign-up"} onClick={() => setMode("sign-up")} type="button">Create patient account</button>
            <button aria-pressed={mode === "sign-in"} onClick={() => setMode("sign-in")} type="button">Sign in</button>
          </div>
          {mode === "sign-up" ? (
            <SignUp routing="hash" signInUrl="/" />
          ) : (
            <SignIn routing="hash" signUpUrl="/" withSignUp={false} />
          )}
        </div>
      </section>
    </main>
  );
}

function PatientSession({ children }: PatientAuthProviderProps) {
  const { getToken } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [state, setState] = useState<"activating" | "ready" | "error">("activating");
  const [message, setMessage] = useState("Linking your assigned synthetic booking…");
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    let active = true;
    setAccessTokenProvider(getToken);
    void activatePatientAccount()
      .then((session) => {
        if (!active) return;
        setState("ready");
        if (pathname === "/sign-in") {
          router.replace(session.onboarding_completed ? "/" : "/onboarding");
          return;
        }
        if (!session.onboarding_completed && pathname !== "/onboarding") {
          router.replace("/onboarding");
        }
      })
      .catch((error: unknown) => {
        if (!active) return;
        setMessage(error instanceof Error ? error.message : "Patient activation failed.");
        setState("error");
      });
    return () => {
      active = false;
      setAccessTokenProvider(null);
    };
  }, [getToken, pathname, retryKey, router]);

  if (state !== "ready") {
    return (
      <main className={styles.sessionState} role={state === "error" ? "alert" : "status"}>
        <span>{state === "error" ? "Access unavailable" : "Secure patient access"}</span>
        <h1>{state === "error" ? "We could not open your booking" : "Opening your booking"}</h1>
        <p>{message}</p>
        {state === "error" ? (
          <Button
            onClick={() => {
              setState("activating");
              setMessage("Linking your assigned synthetic booking…");
              setRetryKey((current) => current + 1);
            }}
            variant="secondary"
          >
            Try again
          </Button>
        ) : null}
        <UserButton showName />
      </main>
    );
  }

  return <><div className={styles.accountDock}><UserButton showName /></div>{children}</>;
}
