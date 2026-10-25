import { NextRequest, NextResponse } from "next/server";

import { ACCESS_COOKIE, REFRESH_COOKIE } from "@/lib/session";

/** Redirige al login del club si no hay ninguna cookie de sesion. */
export function middleware(req: NextRequest) {
  const hasSession =
    req.cookies.has(ACCESS_COOKIE) || req.cookies.has(REFRESH_COOKIE);
  if (!hasSession) {
    // req.url puede llevar el host interno de Next (p. ej. 127.0.0.1) en vez del
    // subdominio del club, asi que la URL se arma con el Host real de la peticion.
    const host = req.headers.get("host") ?? req.nextUrl.host;
    const proto =
      req.headers.get("x-forwarded-proto") ?? req.nextUrl.protocol.replace(":", "");
    return NextResponse.redirect(new URL("/login", `${proto}://${host}`));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
