"use client";

import { ClerkProvider, useAuth } from "@clerk/nextjs";
import { useEffect } from "react";

import { setAccessTokenProvider } from "@/lib/api";

type AuthProviderProps = {
  children: React.ReactNode;
};

export function AuthProvider({ children }: AuthProviderProps) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

  if (!publishableKey) {
    return children;
  }

  return (
    <ClerkProvider publishableKey={publishableKey}>
      <ClerkTokenBridge>{children}</ClerkTokenBridge>
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
