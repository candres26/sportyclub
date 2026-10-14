import { NextRequest, NextResponse } from "next/server";

import {
  REFRESH_COOKIE,
  apiBaseUrl,
  clearTokenCookies,
  tenantHost,
} from "@/lib/session";

export async function POST(req: NextRequest) {
  const refreshToken = req.cookies.get(REFRESH_COOKIE)?.value;
  if (refreshToken) {
    await fetch(`${apiBaseUrl()}/api/v1/auth/logout`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-forwarded-host": tenantHost(req),
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: "no-store",
    }).catch(() => undefined);
  }

  const res = NextResponse.json({ ok: true });
  clearTokenCookies(res);
  return res;
}
