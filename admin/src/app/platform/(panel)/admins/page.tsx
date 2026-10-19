"use client";

import { useEffect, useState } from "react";

import { platformFetch } from "@/lib/platform-client";
import type { PlatformAdmin, PlatformMe } from "@/lib/types";

export default function PlatformAdminsPage() {
  const [admins, setAdmins] = useState<PlatformAdmin[]>([]);
  const [me, setMe] = useState<PlatformMe | null>(null);
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function load() {
    try {
      const [list, current] = await Promise.all([
        platformFetch<PlatformAdmin[]>("admins"),
        platformFetch<PlatformMe>("auth/me"),
      ]);
      setAdmins(list);
      setMe(current);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function onCreate(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setSaving(true);
    try {
      await platformFetch<PlatformAdmin>("admins", {
        method: "POST",
        body: JSON.stringify({ email, full_name: fullName, password }),
      });
      setNotice(`Administrador ${email} creado`);
      setEmail("");
      setFullName("");
      setPassword("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear");
    } finally {
      setSaving(false);
    }
  }

  async function toggle(admin: PlatformAdmin) {
    setError(null);
    setNotice(null);
    try {
      await platformFetch<PlatformAdmin>(`admins/${admin.id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: !admin.is_active }),
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al actualizar");
    }
  }

  return (
    <div className="space-y-6">
      <div className="card">
        <h1 className="mb-4 text-lg font-semibold">Nuevo administrador</h1>
        <form onSubmit={onCreate} className="grid gap-4 sm:grid-cols-3">
          <div>
            <label className="label" htmlFor="full_name">
              Nombre
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
            <label className="label" htmlFor="email">
              Correo
            </label>
            <input
              id="email"
              type="email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
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
          <div className="sm:col-span-3">
            <button className="btn-primary" disabled={saving}>
              {saving ? "Creando..." : "Crear administrador"}
            </button>
          </div>
        </form>
        {notice && <p className="mt-3 text-sm text-green-700">{notice}</p>}
        {error && <p className="error mt-3">{error}</p>}
      </div>

      <div className="card">
        <h2 className="mb-4 font-semibold">Administradores de plataforma</h2>
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-slate-400">
            <tr>
              <th className="py-2">Nombre</th>
              <th className="py-2">Correo</th>
              <th className="py-2">Estado</th>
              <th className="py-2"></th>
            </tr>
          </thead>
          <tbody>
            {admins.map((admin) => (
              <tr key={admin.id} className="border-t border-slate-100">
                <td className="py-2">
                  {admin.full_name}
                  {admin.id === me?.id && (
                    <span className="ml-2 text-xs text-slate-400">(tu)</span>
                  )}
                </td>
                <td className="py-2 text-slate-500">{admin.email}</td>
                <td className="py-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs ${
                      admin.is_active
                        ? "bg-green-100 text-green-700"
                        : "bg-slate-100 text-slate-500"
                    }`}
                  >
                    {admin.is_active ? "activo" : "inactivo"}
                  </span>
                </td>
                <td className="py-2 text-right">
                  {admin.id !== me?.id && (
                    <button
                      className="text-xs text-brand-600 hover:underline"
                      onClick={() => toggle(admin)}
                    >
                      {admin.is_active ? "Desactivar" : "Activar"}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
