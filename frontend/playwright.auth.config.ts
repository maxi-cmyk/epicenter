import { defineConfig } from "@playwright/test";
import { resolve } from "node:path";

const frontendRoot = __dirname;
const repositoryRoot = resolve(frontendRoot, "..");

process.loadEnvFile(resolve(frontendRoot, "nurse/.env.local"));
process.loadEnvFile(resolve(repositoryRoot, "backend/.env"));
process.env.CLERK_PUBLISHABLE_KEY ??= process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

export default defineConfig({
  testDir: "./tests/auth-live",
  fullyParallel: false,
  workers: 1,
  timeout: 45_000,
  expect: { timeout: 15_000 },
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:3001",
    headless: true,
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "setup",
      testMatch: /.*\.setup\.ts/,
    },
    {
      name: "auth-live",
      dependencies: ["setup"],
      testIgnore: /.*\.setup\.ts/,
    },
  ],
  webServer: [
    {
      command: ".venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000",
      cwd: resolve(repositoryRoot, "backend"),
      url: "http://127.0.0.1:8000/healthz",
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      command: "npm run dev:nurse",
      cwd: frontendRoot,
      url: "http://localhost:3001",
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      command: "npm run dev:patient",
      cwd: frontendRoot,
      url: "http://localhost:3000",
      reuseExistingServer: true,
      timeout: 30_000,
    },
  ],
});
