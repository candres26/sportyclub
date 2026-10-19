import { NextRequest, NextResponse } from "next/server";

import { apiBaseUrl } from "@/lib/session";
import {
  PLATFORM_REFRESH_COOKIE,
  clearPlatformTokenCookies,
} from "@/lib/platform-session";

export async function POST(req: NextRequest) {
  const refreshToken = req.cookies.get(PLATFORM_REFRESH_COOKIE)?.value;
  if (refreshToken) {
    await fetch(`${apiBaseUrl()}/api/v1/platform/auth/logout`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: "no-store",
    }).catch(() => undefined);
  }

  const res = NextResponse.json({ ok: true });
  clearPlatformTokenCookies(res);
  return res;
}
