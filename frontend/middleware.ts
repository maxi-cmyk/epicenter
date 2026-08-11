import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Epicenter runs as two separate frontend processes against the same
// codebase: the patient screen (APP_ROLE=patient, port 3000) and the
// nurse/staff screen (APP_ROLE=nurse, port 3001). This middleware is the
// hard boundary between them — it redirects any route the current role
// isn't allowed to reach, regardless of what the nav renders.
const ROUTES_BY_ROLE = {
  patient: ["/pre-arrival"],
  nurse: ["/", "/review", "/kiosk"],
} as const;

const DEFAULT_ROUTE_BY_ROLE = {
  patient: "/pre-arrival",
  nurse: "/",
} as const;

export function middleware(request: NextRequest) {
  const role = process.env.APP_ROLE;

  // No APP_ROLE set (plain `next dev`/`next build`) keeps every route
  // reachable, so local testing, CI, and single-process demos are unaffected.
  if (role !== "patient" && role !== "nurse") {
    return NextResponse.next();
  }

  const { pathname } = request.nextUrl;
  const allowedRoutes: readonly string[] = ROUTES_BY_ROLE[role];

  if (allowedRoutes.includes(pathname)) {
    return NextResponse.next();
  }

  return NextResponse.redirect(new URL(DEFAULT_ROUTE_BY_ROLE[role], request.url));
}

export const config = {
  matcher: ["/((?!_next|.*\\..*).*)"],
};
