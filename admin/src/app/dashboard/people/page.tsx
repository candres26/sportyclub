"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "@/lib/client";
import { DOCUMENT_TYPES, compact, fullName } from "@/lib/people";
import type { Page, Person } from "@/lib/types";

const PAGE_SIZE = 25;

const emptyForm = {
  first_name: "",
  last_name: "",
  document_type: "",
  document_number: "",
  birth_date: "",
  phone: "",
  email: "",
};

export default function PeoplePage() {
  const [page, setPage] = useState<Page<Person> | null>(null);
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const params = new URLSearchParams({
        limit: String(PAGE_SIZE),
        offset: String(offset),
      });
      if (query.trim()) params.set("q", query.trim());
      setPage(await apiFetch<Page<Person>>(`people?${params}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar");
    }
  }, [query, offset]);

  useEffect(() => {
    const timer = setTimeout(load, 250);
    return () => clearTimeout(timer);
  }, [load]);

  function update(field: keyof typeof emptyForm, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function onCreate(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setSaving(true);
    try {
      const person = await apiFetch<Person>("people", {
        method: "POST",
        body: JSON.stringify(compact(form)),
      });
      setNotice(`${fullName(person)} registrado`);
      setForm(emptyForm);
      setShowForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al registrar");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h1 className="text-lg font-semibold">Deportistas y acudientes</h1>
          <button className="btn-primary" onClick={() => setShowForm((v) => !v)}>
            {showForm ? "Cancelar" : "Registrar persona"}
          </button>
        </div>

        {showForm && (
          <form onSubmit={onCreate} className="mb-4 grid gap-3 sm:grid-cols-2">
            <div>
              <label className="label" htmlFor="first_name">Nombres</label>
              <input id="first_name" className="input" value={form.first_name}
                onChange={(e) => update("first_name", e.target.value)} required />
            </div>
            <div>
              <label className="label" htmlFor="last_name">Apellidos</label>
              <input id="last_name" className="input" value={form.last_name}
                onChange={(e) => update("last_name", e.target.value)} required />
            </div>
            <div>
              <label className="label" htmlFor="document_type">Tipo de documento</label>
              <select id="document_type" className="input" value={form.document_type}
                onChange={(e) => update("document_type", e.target.value)}>
                <option value="">-</option>
                {DOCUMENT_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label" htmlFor="document_number">Numero de documento</label>
              <input id="document_number" className="input" value={form.document_number}
                onChange={(e) => update("document_number", e.target.value)} />
            </div>
            <div>
              <label className="label" htmlFor="birth_date">Fecha de nacimiento</label>
              <input id="birth_date" type="date" className="input" value={form.birth_date}
                onChange={(e) => update("birth_date", e.target.value)} />
            </div>
            <div>
              <label className="label" htmlFor="phone">Telefono</label>
              <input id="phone" className="input" value={form.phone}
                onChange={(e) => update("phone", e.target.value)} />
            </div>
            <div className="sm:col-span-2">
              <label className="label" htmlFor="email">Correo</label>
              <input id="email" type="email" className="input" value={form.email}
                onChange={(e) => update("email", e.target.value)} />
            </div>
            <div className="sm:col-span-2">
              <button className="btn-primary" disabled={saving}>
                {saving ? "Guardando..." : "Guardar"}
              </button>
            </div>
          </form>
        )}

        <input
          className="input"
          placeholder="Buscar por nombre o documento"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOffset(0);
          }}
        />
        {notice && <p className="mt-3 text-sm text-green-700">{notice}</p>}
        {error && <p className="error mt-3">{error}</p>}
      </div>

      <div className="card">
        {!page ? (
          <p className="text-sm text-slate-500">Cargando...</p>
        ) : page.items.length === 0 ? (
          <p className="text-sm text-slate-500">No hay personas registradas.</p>
        ) : (
          <>
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-slate-400">
                <tr>
                  <th className="py-2">Nombre</th>
                  <th className="py-2">Documento</th>
                  <th className="py-2">Edad</th>
                  <th className="py-2">Estado</th>
                </tr>
              </thead>
              <tbody>
                {page.items.map((person) => (
                  <tr key={person.id} className="border-t border-slate-100">
                    <td className="py-2">
                      <Link href={`/dashboard/people/${person.id}`}
                        className="text-brand-700 hover:underline">
                        {fullName(person)}
                      </Link>
                    </td>
                    <td className="py-2 text-slate-500">
                      {person.document_number
                        ? `${person.document_type ?? ""} ${person.document_number}`.trim()
                        : "-"}
                    </td>
                    <td className="py-2 text-slate-500">{person.age ?? "-"}</td>
                    <td className="py-2">{person.is_active ? "activo" : "inactivo"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="mt-4 flex items-center justify-between text-sm text-slate-500">
              <span>
                {page.offset + 1}-{page.offset + page.items.length} de {page.total}
              </span>
              <div className="flex gap-2">
                <button className="btn-ghost" disabled={offset === 0}
                  onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>
                  Anterior
                </button>
                <button className="btn-ghost"
                  disabled={page.offset + page.items.length >= page.total}
                  onClick={() => setOffset(offset + PAGE_SIZE)}>
                  Siguiente
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
