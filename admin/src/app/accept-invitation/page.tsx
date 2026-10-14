"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

function AcceptInvitationForm() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token") ?? "";
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/auth/accept-invitation", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ token, full_name: fullName, password }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? "No se pudo aceptar la invitacion");
      }
      router.push("/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card w-full max-w-sm">
      <h1 className="text-xl font-semibold text-brand-700">Unete a tu club</h1>
      <p className="mb-6 text-sm text-slate-500">Completa tu registro</p>

      {!token && <p className="error mb-4">Falta el token de invitacion</p>}

      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="label" htmlFor="full_name">
            Nombre completo
          </label>
          <input
            id="full_name"
            className="input"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="label" htmlFor="password">
            Contrasena
          </label>
          <input
            id="password"
            type="password"
            className="input"
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        {error && <p className="error">{error}</p>}

        <button className="btn-primary w-full" disabled={loading || !token}>
          {loading ? "Creando cuenta..." : "Crear cuenta"}
        </button>
      </form>
    </div>
  );
}

export default function AcceptInvitationPage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Suspense fallback={<div className="card w-full max-w-sm">Cargando...</div>}>
        <AcceptInvitationForm />
      </Suspense>
    </main>
  );
}
