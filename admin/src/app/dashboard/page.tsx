"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/client";
import type { Invitation, Me, Page, Role, User } from "@/lib/types";

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="card">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-3xl font-semibold text-brand-700">{value}</p>
    </div>
  );
}

export default function DashboardHome() {
  const [me, setMe] = useState<Me | null>(null);
  const [counts, setCounts] = useState({ users: "-", roles: "-", invitations: "-" });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<Me>("auth/me").then(setMe).catch(() => undefined);

    apiFetch<User[]>("users")
      .then((users) => setCounts((c) => ({ ...c, users: String(users.length) })))
      .catch(() => setError("No tienes permiso para ver usuarios"));

    apiFetch<Role[]>("roles")
      .then((roles) => setCounts((c) => ({ ...c, roles: String(roles.length) })))
      .catch(() => undefined);

    apiFetch<Page<Invitation>>("invitations")
      .then((page) => setCounts((c) => ({ ...c, invitations: String(page.total ?? page.items.length) })))
      .catch(() => undefined);
  }, []);

  return (
    <div className="space-y-6">
      <div className="card">
        <h1 className="text-lg font-semibold">Hola{me ? `, ${me.full_name}` : ""}</h1>
        <p className="text-sm text-slate-500">
          {me ? `Club ${me.tenant.name} (${me.tenant.slug})` : "Cargando informacion..."}
        </p>
        {me && (
          <p className="mt-2 text-xs text-slate-400">
            Roles: {me.roles.join(", ") || "sin roles"}
          </p>
        )}
      </div>

      {error && <p className="error">{error}</p>}

      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label="Usuarios" value={counts.users} />
        <Stat label="Roles" value={counts.roles} />
        <Stat label="Invitaciones pendientes" value={counts.invitations} />
      </div>
    </div>
  );
}
