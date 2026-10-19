import { NextRequest, NextResponse } from "next/server";

import { apiBaseUrl } from "@/lib/session";
import {
  PLATFORM_ACCESS_COOKIE,
  PLATFORM_REFRESH_COOKIE,
  clearPlatformTokenCookies,
  setPlatformTokenCookies,
} from "@/lib/platform-session";

type TokenPair = { access_token: string; refresh_token: string; expires_in: number };

async function callBackend(
  req: NextRequest,
  path: string[],
  access: string | undefined,
): Promise<Response> {
  const url = `${apiBaseUrl()}/api/v1/platform/${path.join("/")}${req.nextUrl.search}`;
  const headers: Record<string, string> = {};
  const contentType = req.headers.get("content-type");
  if (contentType) headers["content-type"] = contentType;
  if (access) headers["authorization"] = `Bearer ${access}`;

  const method = req.method;
  const body = method === "GET" || method === "HEAD" ? undefined : await req.text();

  return fetch(url, { method, headers, body, cache: "no-store" });
}

async function refreshTokens(req: NextRequest): Promise<TokenPair | null> {
  const refreshToken = req.cookies.get(PLATFORM_REFRESH_COOKIE)?.value;
  if (!refreshToken) return null;

  const res = await fetch(`${apiBaseUrl()}/api/v1/platform/auth/refresh`, {
    method: "POST",
    headers: { "content-type": "application/json" },
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
  let access = req.cookies.get(PLATFORM_ACCESS_COOKIE)?.value;

  let backend = await callBackend(req, path, access);
  let refreshed: TokenPair | null = null;

  const isRefreshCall = path.join("/") === "auth/refresh";
  if (backend.status === 401 && !isRefreshCall) {
    refreshed = await refreshTokens(req);
    if (refreshed) {
      access = refreshed.access_token;
      backend = await callBackend(req, path, access);
    }
  }

  const text = await backend.text();
  const res = new NextResponse(text || null, {
    status: backend.status,
    headers: {
      "content-type": backend.headers.get("content-type") ?? "application/json",
    },
  });

  if (refreshed) setPlatformTokenCookies(res, refreshed);
  if (backend.status === 401 && !refreshed) clearPlatformTokenCookies(res);
  return res;
}

export {
  handler as DELETE,
  handler as GET,
  handler as PATCH,
  handler as POST,
  handler as PUT,
};
