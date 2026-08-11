export type AppRole = "patient" | "nurse" | "combined";

/**
 * `APP_ROLE` is set per dev/build process (see package.json `dev:patient` /
 * `dev:nurse` scripts) so the same codebase can run as two separate
 * processes on two separate ports. "combined" is the fallback for plain
 * `next dev`/`next build`/tests, where every route stays reachable.
 */
export function getAppRole(): AppRole {
  const value = process.env.APP_ROLE;
  return value === "patient" || value === "nurse" ? value : "combined";
}
