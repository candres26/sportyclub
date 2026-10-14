"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/client";
import type { User } from "@/lib/types";

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<User[]>("users")
      .then(setUsers)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="card">
      <h1 className="mb-4 text-lg font-semibold">Usuarios del club</h1>
      {error && <p className="error mb-4">{error}</p>}
      {loading ? (
        <p className="text-sm text-slate-500">Cargando...</p>
      ) : users.length === 0 ? (
        <p className="text-sm text-slate-500">Sin usuarios.</p>
      ) : (
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-slate-400">
            <tr>
              <th className="py-2">Nombre</th>
              <th className="py-2">Correo</th>
              <th className="py-2">Roles</th>
              <th className="py-2">Estado</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id} className="border-t border-slate-100">
                <td className="py-2">{user.full_name}</td>
                <td className="py-2 text-slate-500">{user.email}</td>
                <td className="py-2">{user.roles.join(", ") || "-"}</td>
                <td className="py-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs ${
                      user.is_active
                        ? "bg-green-100 text-green-700"
                        : "bg-slate-100 text-slate-500"
                    }`}
                  >
                    {user.is_active ? "activo" : "inactivo"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
