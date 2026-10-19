import { ApiError, extractDetail } from "./client";

export async function platformFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`/api/platform/proxy/${path}`, {
    ...options,
    headers: { "content-type": "application/json", ...(options.headers ?? {}) },
  });

  if (res.status === 204) return null as T;
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(extractDetail(data), res.status);
  return data as T;
}
