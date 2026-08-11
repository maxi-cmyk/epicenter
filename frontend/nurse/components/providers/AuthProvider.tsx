"use client";

import { ClerkLoaded, ClerkLoading, ClerkProvider, Show, UserButton, useAuth } from "@clerk/nextjs";
import { useEffect } from "react";

import { setAccessTokenProvider } from "@/lib/api";

import { StaffSignIn } from "./StaffSignIn";
import styles from "./AuthProvider.module.css";

type AuthProviderProps = {
  children: React.ReactNode;
};

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
          <ClerkTokenBridge>
            <div className={styles.accountDock}>
              <UserButton showName />
            </div>
            {children}
          </ClerkTokenBridge>
        </Show>
      </ClerkLoaded>
    </ClerkProvider>
  );
}

function ClerkTokenBridge({ children }: AuthProviderProps) {
  const { getToken } = useAuth();

  useEffect(() => {
    setAccessTokenProvider(getToken);
    return () => setAccessTokenProvider(null);
  }, [getToken]);

  return children;
}
