import { NextRequest, NextResponse } from "next/server";

import {
  ACCESS_COOKIE,
  REFRESH_COOKIE,
  apiBaseUrl,
  clearTokenCookies,
  setTokenCookies,
  tenantHost,
} from "@/lib/session";

type TokenPair = { access_token: string; refresh_token: string; expires_in: number };

async function callBackend(
  req: NextRequest,
  path: string[],
  access: string | undefined,
  host: string,
): Promise<Response> {
  const url = `${apiBaseUrl()}/api/v1/${path.join("/")}${req.nextUrl.search}`;
  const headers: Record<string, string> = { "x-forwarded-host": host };
  const contentType = req.headers.get("content-type");
  if (contentType) headers["content-type"] = contentType;
  if (access) headers["authorization"] = `Bearer ${access}`;

  const method = req.method;
  const body = method === "GET" || method === "HEAD" ? undefined : await req.text();

  return fetch(url, { method, headers, body, cache: "no-store" });
}

async function refreshTokens(req: NextRequest, host: string): Promise<TokenPair | null> {
  const refreshToken = req.cookies.get(REFRESH_COOKIE)?.value;
  if (!refreshToken) return null;

  const res = await fetch(`${apiBaseUrl()}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-forwarded-host": host },
    body: JSON.stringify({ refresh_token: refreshToken }),
    cache: "no-store",
  });
  if (!res.ok) return null;
  return (await res.json()) as TokenPair;
}

async function handler(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
): Promise<NextResponse> {
  const { path } = await ctx.params;
  const host = tenantHost(req);
  let access = req.cookies.get(ACCESS_COOKIE)?.value;

  let backend = await callBackend(req, path, access, host);
  let refreshed: TokenPair | null = null;

  if (backend.status === 401 && path[0] !== "auth") {
    refreshed = await refreshTokens(req, host);
    if (refreshed) {
      access = refreshed.access_token;
      backend = await callBackend(req, path, access, host);
    }
  }

  const text = await backend.text();
  const res = new NextResponse(text || null, {
    status: backend.status,
    headers: {
      "content-type": backend.headers.get("content-type") ?? "application/json",
    },
  });

  if (refreshed) setTokenCookies(res, refreshed);
  if (backend.status === 401 && !refreshed) clearTokenCookies(res);
  return res;
}

export {
  handler as DELETE,
  handler as GET,
  handler as PATCH,
  handler as POST,
  handler as PUT,
};
