"use client";

import { ClerkLoaded, ClerkLoading, ClerkProvider, Show, UserButton, useAuth } from "@clerk/nextjs";
import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { ApiError, fetchStaffSession, setAccessTokenProvider } from "@/lib/api";

import { StaffSignIn } from "./StaffSignIn";
import styles from "./AuthProvider.module.css";

type AuthProviderProps = {
  children: React.ReactNode;
};

const StaffRoleContext = createContext<string | null>(null);

export function useStaffRole() {
  return useContext(StaffRoleContext);
}

export function AuthProvider({ children }: AuthProviderProps) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  const visualQaBypass =
    process.env.NODE_ENV === "development" && process.env.NEXT_PUBLIC_E2E_BYPASS_AUTH === "true";

  if (visualQaBypass) {
    return children;
  }

  if (!publishableKey) {
    return (
      <main className={styles.authConfigurationError}>
        <span>Configuration required</span>
        <h1>Staff authentication is unavailable</h1>
        <p>
          Add <code>NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY</code> to the frontend environment before opening the clinic
          workspace.
        </p>
      </main>
    );
  }

  return (
    <ClerkProvider
      appearance={{
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
        <div aria-live="polite" className={styles.authLoading}>
          Establishing secure staff access…
        </div>
      </ClerkLoading>
      <ClerkLoaded>
        <Show when="signed-out">
          <StaffSignIn />
        </Show>
        <Show when="signed-in">
          <ClerkTokenBridge>{children}</ClerkTokenBridge>
        </Show>
      </ClerkLoaded>
    </ClerkProvider>
  );
}

function ClerkTokenBridge({ children }: AuthProviderProps) {
  const { getToken } = useAuth();
  const [state, setState] = useState<"checking" | "authorized" | "denied" | "error">("checking");
  const [message, setMessage] = useState("Confirming your clinic role…");
  const [role, setRole] = useState<string | null>(null);

  const verifyAccess = useCallback(async () => {
    setState("checking");
    setMessage("Confirming your clinic role…");
    try {
      const session = await fetchStaffSession();
      setRole(session.role);
      setState("authorized");
    } catch (error: unknown) {
      if (error instanceof ApiError && error.status === 403) {
        setMessage(
          "This account is not mapped to an active nurse role. Contact your clinic administrator, then try again.",
        );
        setState("denied");
        return;
      }
      setMessage("Clinic authorization could not be verified. Check the API connection, then try again.");
      setState("error");
    }
  }, []);

  useEffect(() => {
    let active = true;
    setAccessTokenProvider(getToken);
    queueMicrotask(() => {
      if (active) void verifyAccess();
    });
    return () => {
      active = false;
      setAccessTokenProvider(null);
    };
  }, [getToken, verifyAccess]);

  if (state !== "authorized") {
    return (
      <main className={styles.staffAccessState} role={state === "checking" ? "status" : "alert"}>
        <span>{state === "checking" ? "Staff authorization" : "Access denied"}</span>
        <h1>{state === "checking" ? "Checking clinic access" : "Nurse access required"}</h1>
        <p>{message}</p>
        <div className={styles.staffAccessActions}>
          {state !== "checking" ? (
            <button className={styles.retryAccessButton} onClick={() => void verifyAccess()} type="button">
              Try again
            </button>
          ) : null}
          <UserButton showName />
        </div>
      </main>
    );
  }

  return <StaffRoleContext.Provider value={role}>{children}</StaffRoleContext.Provider>;
}
