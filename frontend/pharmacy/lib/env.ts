const DEFAULT_API_URL = "http://localhost:8000/api/v1";

export function validatePharmacyEnvironment() {
  const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_URL;

  try {
    const parsed = new URL(apiUrl);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") throw new Error("unsupported protocol");
  } catch {
    throw new Error("NEXT_PUBLIC_API_BASE_URL must be an absolute HTTP(S) URL for the pharmacy panel.");
  }

  return {
    apiUrl,
    clerkConfigured: Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY),
  };
}
