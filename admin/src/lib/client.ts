export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export function extractDetail(data: unknown): string {
  if (data && typeof data === "object" && "detail" in data) {
    const detail = (data as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) => (item as { msg?: string }).msg ?? "dato invalido")
        .join(", ");
    }
  }
  return "Ocurrio un error inesperado";
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`/api/proxy/${path}`, {
    ...options,
    headers: { "content-type": "application/json", ...(options.headers ?? {}) },
  });

  if (res.status === 204) return null as T;
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(extractDetail(data), res.status);
  return data as T;
}
