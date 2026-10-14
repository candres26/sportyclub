import type { NextRequest, NextResponse } from "next/server";

export const ACCESS_COOKIE = "sc_access";
export const REFRESH_COOKIE = "sc_refresh";

const REFRESH_MAX_AGE = 60 * 60 * 24 * 30;

export function apiBaseUrl(): string {
  return process.env.API_BASE_URL ?? "http://localhost:8000";
}

export function baseDomain(): string {
  return process.env.BASE_DOMAIN ?? "lvh.me";
}

/** Deriva el host del club (subdominio) a partir del Host del panel. */
export function tenantHost(req: NextRequest): string {
  const host = req.headers.get("host") ?? "";
  const sub = host.split(":")[0].split(".")[0] || "www";
  return `${sub}.${baseDomain()}`;
}

const cookieOptions = {
  httpOnly: true,
  sameSite: "lax" as const,
  secure: process.env.NODE_ENV === "production",
  path: "/",
};

export function setTokenCookies(
  res: NextResponse,
  tokens: { access_token: string; refresh_token: string; expires_in: number },
): void {
  res.cookies.set(ACCESS_COOKIE, tokens.access_token, {
    ...cookieOptions,
    maxAge: tokens.expires_in,
  });
  res.cookies.set(REFRESH_COOKIE, tokens.refresh_token, {
    ...cookieOptions,
    maxAge: REFRESH_MAX_AGE,
  });
}

export function clearTokenCookies(res: NextResponse): void {
  res.cookies.set(ACCESS_COOKIE, "", { ...cookieOptions, maxAge: 0 });
  res.cookies.set(REFRESH_COOKIE, "", { ...cookieOptions, maxAge: 0 });
}
