import { NextRequest, NextResponse } from "next/server";

import { apiBaseUrl, setTokenCookies, tenantHost } from "@/lib/session";

export async function POST(req: NextRequest) {
  const body = await req.text();
  const backend = await fetch(`${apiBaseUrl()}/api/v1/auth/accept-invitation`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-forwarded-host": tenantHost(req),
    },
    body,
    cache: "no-store",
  });

  const data = await backend.json().catch(() => ({}));
  if (!backend.ok) {
    return NextResponse.json(data, { status: backend.status });
  }

  const res = NextResponse.json({ ok: true });
  setTokenCookies(res, data);
  return res;
}
