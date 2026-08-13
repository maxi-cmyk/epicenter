import { loadEnvConfig } from "@next/env";
import type { NextConfig } from "next";
import path from "node:path";

const appDir = process.cwd();
loadEnvConfig(path.resolve(appDir, ".."));
loadEnvConfig(appDir);

const nextConfig: NextConfig = {
  agentRules: false,
  reactStrictMode: true,
  transpilePackages: ["@epicenter/shared"],
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "",
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ?? "",
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL ?? "",
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? "",
  },
};

export default nextConfig;
