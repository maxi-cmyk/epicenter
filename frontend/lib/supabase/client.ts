"use client";

import { useSession } from "@clerk/nextjs";
import { createBrowserClient } from "@supabase/ssr";
import { useMemo } from "react";

import type { Database } from "./database.types";

export function useSupabaseClient() {
  const { session } = useSession();
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const publishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

  return useMemo(() => {
    if (!url || !publishableKey) {
      return null;
    }

    return createBrowserClient<Database>(url, publishableKey, {
      accessToken: async () => session?.getToken() ?? null,
    });
  }, [publishableKey, session, url]);
}
