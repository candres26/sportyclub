import { NextRequest, NextResponse } from "next/server";

import { ACCESS_COOKIE, REFRESH_COOKIE } from "@/lib/session";

const BASE_DOMAIN = (process.env.NEXT_PUBLIC_BASE_DOMAIN ?? "lvh.me").toLowerCase();

/** Slug del club segun el subdominio; null en el dominio raiz (igual que el backend). */
function clubSlug(host: string): string | null {
  const hostname = host.split(":")[0].toLowerCase();
  if (hostname === BASE_DOMAIN || hostname === `www.${BASE_DOMAIN}`) return null;
  if (!hostname.endsWith(`.${BASE_DOMAIN}`)) return null;
  return hostname.slice(0, -(BASE_DOMAIN.length + 1)).split(".")[0] || null;
}

function redirectTo(req: NextRequest, host: string, pathname: string) {
  // req.url puede llevar el host interno de Next (p. ej. 127.0.0.1) en vez del
  // subdominio del club, asi que la URL se arma con el Host real de la peticion.
  const proto =
    req.headers.get("x-forwarded-proto") ?? req.nextUrl.protocol.replace(":", "");
  return NextResponse.redirect(new URL(pathname, `${proto}://${host}`));
}

export function middleware(req: NextRequest) {
  const host = req.headers.get("host") ?? req.nextUrl.host;
  const { pathname } = req.nextUrl;

  // Sin subdominio no hay club: el dominio raiz es del panel de plataforma.
  if (clubSlug(host) === null) {
    return redirectTo(req, host, "/platform");
  }

  const hasSession =
    req.cookies.has(ACCESS_COOKIE) || req.cookies.has(REFRESH_COOKIE);
  if (pathname.startsWith("/dashboard") && !hasSession) {
    return redirectTo(req, host, "/login");
  }
  return NextResponse.next();
}

export const config = {
  // Rutas del panel del club; /platform y /api quedan fuera.
  matcher: ["/", "/login", "/accept-invitation", "/dashboard/:path*"],
};
