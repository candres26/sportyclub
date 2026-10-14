"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/client";
import type { Invitation, Role } from "@/lib/types";

export default function InvitationsPage() {
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [email, setEmail] = useState("");
  const [roleId, setRoleId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  async function load() {
    try {
      const [list, roleList] = await Promise.all([
        apiFetch<Invitation[]>("invitations"),
        apiFetch<Role[]>("roles"),
      ]);
      setInvitations(list);
      setRoles(roleList);
      if (!roleId && roleList.length > 0) setRoleId(roleList[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setSending(true);
    try {
      await apiFetch("invitations", {
        method: "POST",
        body: JSON.stringify({ email, role_id: roleId }),
      });
      setNotice(`Invitacion enviada a ${email}`);
      setEmail("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al invitar");
    } finally {
      setSending(false);
    }
  }

  async function revoke(id: string) {
    try {
      await apiFetch(`invitations/${id}`, { method: "DELETE" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al revocar");
    }
  }

  return (
    <div className="space-y-6">
      <div className="card">
        <h1 className="mb-4 text-lg font-semibold">Invitar usuario</h1>
        <form onSubmit={onSubmit} className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1">
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
          <div className="sm:w-48">
            <label className="label" htmlFor="role">
              Rol
            </label>
            <select
              id="role"
              className="input"
              value={roleId}
              onChange={(e) => setRoleId(e.target.value)}
            >
              {roles.map((role) => (
                <option key={role.id} value={role.id}>
                  {role.name}
                </option>
              ))}
            </select>
          </div>
          <button className="btn-primary" disabled={sending || !roleId}>
            {sending ? "Enviando..." : "Invitar"}
          </button>
        </form>
        {notice && <p className="mt-3 text-sm text-green-700">{notice}</p>}
        {error && <p className="error mt-3">{error}</p>}
      </div>

      <div className="card">
        <h2 className="mb-4 font-semibold">Invitaciones</h2>
        {invitations.length === 0 ? (
          <p className="text-sm text-slate-500">No hay invitaciones.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-400">
              <tr>
                <th className="py-2">Correo</th>
                <th className="py-2">Rol</th>
                <th className="py-2">Estado</th>
                <th className="py-2"></th>
              </tr>
            </thead>
            <tbody>
              {invitations.map((invitation) => (
                <tr key={invitation.id} className="border-t border-slate-100">
                  <td className="py-2">{invitation.email}</td>
                  <td className="py-2 text-slate-500">{invitation.role_name ?? "-"}</td>
                  <td className="py-2">
                    {invitation.accepted_at ? "aceptada" : "pendiente"}
                  </td>
                  <td className="py-2 text-right">
                    {!invitation.accepted_at && (
                      <button
                        className="text-xs text-red-600 hover:underline"
                        onClick={() => revoke(invitation.id)}
                      >
                        Revocar
                      </button>
                    )}
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
