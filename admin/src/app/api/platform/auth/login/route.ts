import { NextRequest, NextResponse } from "next/server";

import { apiBaseUrl } from "@/lib/session";
import { setPlatformTokenCookies } from "@/lib/platform-session";

export async function POST(req: NextRequest) {
  const body = await req.text();
  const backend = await fetch(`${apiBaseUrl()}/api/v1/platform/auth/login`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body,
    cache: "no-store",
  });

  const data = await backend.json().catch(() => ({}));
  if (!backend.ok) {
    return NextResponse.json(data, { status: backend.status });
  }

  const res = NextResponse.json({ ok: true });
  setPlatformTokenCookies(res, data);
  return res;
}
