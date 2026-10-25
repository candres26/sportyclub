export const BASE_DOMAIN = (process.env.NEXT_PUBLIC_BASE_DOMAIN ?? "lvh.me").toLowerCase();

/** Slug del club segun el subdominio; null en el dominio raiz (igual que el backend). */
export function clubSlug(host: string): string | null {
  const hostname = host.split(":")[0].toLowerCase();
  if (hostname === BASE_DOMAIN || hostname === `www.${BASE_DOMAIN}`) return null;
  if (!hostname.endsWith(`.${BASE_DOMAIN}`)) return null;
  return hostname.slice(0, -(BASE_DOMAIN.length + 1)).split(".")[0] || null;
}
