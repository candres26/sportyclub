"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/client";
import type { Role } from "@/lib/types";

export default function RolesPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<Role[]>("roles")
      .then(setRoles)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-semibold">Roles y permisos</h1>
      {error && <p className="error">{error}</p>}
      {loading ? (
        <p className="text-sm text-slate-500">Cargando...</p>
      ) : (
        roles.map((role) => (
          <div key={role.id} className="card">
            <div className="flex items-center justify-between">
              <h2 className="font-medium text-slate-800">{role.name}</h2>
              {role.is_system && (
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                  sistema
                </span>
              )}
            </div>
            {role.description && (
              <p className="mt-1 text-sm text-slate-500">{role.description}</p>
            )}
            <div className="mt-3 flex flex-wrap gap-1">
              {role.permissions.map((permission) => (
                <span
                  key={permission}
                  className="rounded-md bg-brand-50 px-2 py-0.5 text-xs text-brand-700"
                >
                  {permission}
                </span>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
