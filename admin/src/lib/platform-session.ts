import type { NextResponse } from "next/server";

export const PLATFORM_ACCESS_COOKIE = "sp_access";
export const PLATFORM_REFRESH_COOKIE = "sp_refresh";

const REFRESH_MAX_AGE = 60 * 60 * 24 * 30;

const cookieOptions = {
  httpOnly: true,
  sameSite: "lax" as const,
  secure: process.env.NODE_ENV === "production",
  path: "/",
};

export function setPlatformTokenCookies(
  res: NextResponse,
  tokens: { access_token: string; refresh_token: string; expires_in: number },
): void {
  res.cookies.set(PLATFORM_ACCESS_COOKIE, tokens.access_token, {
    ...cookieOptions,
    maxAge: tokens.expires_in,
  });
  res.cookies.set(PLATFORM_REFRESH_COOKIE, tokens.refresh_token, {
    ...cookieOptions,
    maxAge: REFRESH_MAX_AGE,
  });
}

export function clearPlatformTokenCookies(res: NextResponse): void {
  res.cookies.set(PLATFORM_ACCESS_COOKIE, "", { ...cookieOptions, maxAge: 0 });
  res.cookies.set(PLATFORM_REFRESH_COOKIE, "", { ...cookieOptions, maxAge: 0 });
}
