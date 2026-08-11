import type { NextConfig } from "next";

// Running the patient (3000) and nurse (3001) dev servers as two separate
// `next dev` processes against the same checkout needs separate build caches,
// or one process's Turbopack cache clobbers the other's mid-request.
const appRole = process.env.APP_ROLE;
const distDir = appRole === "patient" ? ".next-patient" : appRole === "nurse" ? ".next-nurse" : ".next";

const nextConfig: NextConfig = {
  agentRules: false,
  reactStrictMode: true,
  distDir,
};

export default nextConfig;
