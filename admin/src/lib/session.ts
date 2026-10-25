import type { NextRequest, NextResponse } from "next/server";

export const ACCESS_COOKIE = "sc_access";
export const REFRESH_COOKIE = "sc_refresh";

const REFRESH_MAX_AGE = 60 * 60 * 24 * 30;

export function apiBaseUrl(): string {
  return process.env.API_BASE_URL ?? "http://localhost:8000";
}

/**
 * Host que se reenvia a la API para resolver el club. Se pasa el hostname real
 * del panel y el backend extrae el subdominio respecto a BASE_DOMAIN, igual que
 * cuando la peticion llega por Caddy (sin subdominio responde "club no encontrado").
 */
export function tenantHost(req: NextRequest): string {
  const host = req.headers.get("host") ?? "";
  return host.split(":")[0].toLowerCase();
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
