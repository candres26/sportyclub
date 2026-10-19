"use client";

import { useEffect, useState } from "react";

import { platformFetch } from "@/lib/platform-client";
import type { Club, ClubCreated } from "@/lib/types";

function slugify(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 63);
}

export default function PlatformClubsPage() {
  const [clubs, setClubs] = useState<Club[]>([]);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [ownerEmail, setOwnerEmail] = useState("");
  const [ownerName, setOwnerName] = useState("");
  const [inviteUrl, setInviteUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function load() {
    try {
      setClubs(await platformFetch<Club[]>("clubs"));
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
    setInviteUrl(null);
    setSaving(true);
    try {
      const created = await platformFetch<ClubCreated>("clubs", {
        method: "POST",
        body: JSON.stringify({
          name,
          slug,
          owner_email: ownerEmail || null,
          owner_full_name: ownerName || null,
        }),
      });
      setInviteUrl(created.invite_url);
      setNotice(`Club "${created.name}" creado`);
      setName("");
      setSlug("");
      setOwnerEmail("");
      setOwnerName("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear el club");
    } finally {
      setSaving(false);
    }
  }

  async function toggle(club: Club) {
    setError(null);
    try {
      await platformFetch<Club>(`clubs/${club.id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: !club.is_active }),
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al actualizar");
    }
  }

  async function copyInvite() {
    if (!inviteUrl) return;
    try {
      await navigator.clipboard.writeText(inviteUrl);
      setNotice("Enlace de invitacion copiado");
    } catch {
      setNotice("Copia manualmente el enlace");
    }
  }

  return (
    <div className="space-y-6">
      <div className="card">
        <h1 className="mb-4 text-lg font-semibold">Nuevo club</h1>
        <form onSubmit={onCreate} className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="label" htmlFor="name">
              Nombre
            </label>
            <input
              id="name"
              className="input"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setSlug(slugify(e.target.value));
              }}
              required
            />
          </div>
          <div>
            <label className="label" htmlFor="slug">
              Subdominio
            </label>
            <input
              id="slug"
              className="input"
              value={slug}
              onChange={(e) => setSlug(slugify(e.target.value))}
              placeholder="mi-club"
              required
            />
          </div>
          <div>
            <label className="label" htmlFor="owner_email">
              Correo del dueno
            </label>
            <input
              id="owner_email"
              type="email"
              className="input"
              value={ownerEmail}
              onChange={(e) => setOwnerEmail(e.target.value)}
              placeholder="dueno@club.com"
            />
          </div>
          <div>
            <label className="label" htmlFor="owner_name">
              Nombre del dueno
            </label>
            <input
              id="owner_name"
              className="input"
              value={ownerName}
              onChange={(e) => setOwnerName(e.target.value)}
            />
          </div>
          <div className="sm:col-span-2">
            <button className="btn-primary" disabled={saving}>
              {saving ? "Creando..." : "Crear club"}
            </button>
          </div>
        </form>

        {notice && <p className="mt-3 text-sm text-green-700">{notice}</p>}
        {inviteUrl && (
          <div className="mt-3 rounded-lg bg-brand-50 p-3">
            <p className="text-xs font-medium text-brand-700">
              Enlace de invitacion del dueno
            </p>
            <div className="mt-1 flex items-center gap-2">
              <code className="flex-1 break-all text-xs text-slate-700">
                {inviteUrl}
              </code>
              <button className="btn-ghost" onClick={copyInvite} type="button">
                Copiar
              </button>
            </div>
          </div>
        )}
        {error && <p className="error mt-3">{error}</p>}
      </div>

      <div className="card">
        <h2 className="mb-4 font-semibold">Clubes</h2>
        {clubs.length === 0 ? (
          <p className="text-sm text-slate-500">Todavia no hay clubes.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-400">
              <tr>
                <th className="py-2">Nombre</th>
                <th className="py-2">Subdominio</th>
                <th className="py-2">Estado</th>
                <th className="py-2">Creado</th>
                <th className="py-2"></th>
              </tr>
            </thead>
            <tbody>
              {clubs.map((club) => (
                <tr key={club.id} className="border-t border-slate-100">
                  <td className="py-2">{club.name}</td>
                  <td className="py-2 text-slate-500">{club.slug}</td>
                  <td className="py-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs ${
                        club.is_active
                          ? "bg-green-100 text-green-700"
                          : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {club.is_active ? "activo" : "suspendido"}
                    </span>
                  </td>
                  <td className="py-2 text-slate-500">
                    {new Date(club.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-2 text-right">
                    <button
                      className="text-xs text-brand-600 hover:underline"
                      onClick={() => toggle(club)}
                    >
                      {club.is_active ? "Suspender" : "Activar"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
