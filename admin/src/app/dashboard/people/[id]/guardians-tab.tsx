"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "@/lib/client";
import { RELATIONS, compact, fullName } from "@/lib/people";
import type { Page, Person, RelatedPerson } from "@/lib/types";

const emptyNew = { first_name: "", last_name: "", document_number: "", phone: "" };

export default function GuardiansTab({ person }: { person: Person }) {
  const [guardians, setGuardians] = useState<RelatedPerson[]>([]);
  const [dependents, setDependents] = useState<RelatedPerson[]>([]);
  const [mode, setMode] = useState<"existing" | "new">("existing");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Person[]>([]);
  const [selected, setSelected] = useState<Person | null>(null);
  const [newPerson, setNewPerson] = useState(emptyNew);
  const [relation, setRelation] = useState(RELATIONS[0]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const [g, d] = await Promise.all([
        apiFetch<RelatedPerson[]>(`people/${person.id}/guardians`),
        apiFetch<RelatedPerson[]>(`people/${person.id}/dependents`),
      ]);
      setGuardians(g);
      setDependents(d);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar");
    }
  }, [person.id]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (mode !== "existing" || query.trim().length < 2) {
      setResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const params = new URLSearchParams({ q: query.trim(), limit: "8" });
        const page = await apiFetch<Page<Person>>(`people?${params}`);
        setResults(page.items.filter((p) => p.id !== person.id));
      } catch {
        setResults([]);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [query, mode, person.id]);

  async function onLink(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSaving(true);
    try {
      let guardianId = selected?.id;
      if (mode === "new") {
        const created = await apiFetch<Person>("people", {
          method: "POST",
          body: JSON.stringify(compact(newPerson)),
        });
        guardianId = created.id;
      }
      if (!guardianId) throw new Error("Selecciona una persona");
      await apiFetch(`people/${person.id}/guardians`, {
        method: "POST",
        body: JSON.stringify({ guardian_id: guardianId, relation }),
      });
      setSelected(null);
      setQuery("");
      setNewPerson(emptyNew);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al vincular");
    } finally {
      setSaving(false);
    }
  }

  async function unlink(guardianId: string) {
    setError(null);
    try {
      await apiFetch(`people/${person.id}/guardians/${guardianId}`, { method: "DELETE" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al desvincular");
    }
  }

  return (
    <div className="space-y-4">
      <div className="card">
        <h2 className="mb-3 font-semibold">Acudientes de {person.first_name}</h2>
        {guardians.length === 0 ? (
          <p className="text-sm text-slate-500">Sin acudientes registrados.</p>
        ) : (
          <ul className="divide-y divide-slate-100 text-sm">
            {guardians.map(({ relation: rel, person: g }) => (
              <li key={g.id} className="flex items-center justify-between py-2">
                <span>
                  <Link href={`/dashboard/people/${g.id}`} className="text-brand-700 hover:underline">
                    {fullName(g)}
                  </Link>{" "}
                  <span className="text-slate-500">· {rel}{g.phone ? ` · ${g.phone}` : ""}</span>
                </span>
                <button className="text-xs text-red-600 hover:underline" onClick={() => unlink(g.id)}>
                  Quitar
                </button>
              </li>
            ))}
          </ul>
        )}

        <form onSubmit={onLink} className="mt-4 space-y-3 border-t border-slate-100 pt-4">
          <div className="flex gap-4 text-sm">
            <label className="flex items-center gap-1">
              <input type="radio" checked={mode === "existing"} onChange={() => setMode("existing")} />
              Persona registrada
            </label>
            <label className="flex items-center gap-1">
              <input type="radio" checked={mode === "new"} onChange={() => setMode("new")} />
              Nueva persona
            </label>
          </div>

          {mode === "existing" ? (
            <div>
              {selected ? (
                <p className="text-sm">
                  {fullName(selected)}{" "}
                  <button type="button" className="text-xs text-brand-700 hover:underline"
                    onClick={() => setSelected(null)}>
                    cambiar
                  </button>
                </p>
              ) : (
                <>
                  <input className="input" placeholder="Buscar por nombre o documento"
                    value={query} onChange={(e) => setQuery(e.target.value)} />
                  {results.length > 0 && (
                    <ul className="mt-1 rounded-lg border border-slate-200 text-sm">
                      {results.map((r) => (
                        <li key={r.id}>
                          <button type="button" className="w-full px-3 py-1.5 text-left hover:bg-slate-50"
                            onClick={() => setSelected(r)}>
                            {fullName(r)}
                            {r.document_number && (
                              <span className="text-slate-500"> · {r.document_number}</span>
                            )}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </>
              )}
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {(["first_name", "last_name", "document_number", "phone"] as const).map((f) => (
                <input key={f} className="input" required={f === "first_name" || f === "last_name"}
                  placeholder={{ first_name: "Nombres", last_name: "Apellidos",
                    document_number: "Documento", phone: "Telefono" }[f]}
                  value={newPerson[f]}
                  onChange={(e) => setNewPerson({ ...newPerson, [f]: e.target.value })} />
              ))}
            </div>
          )}

          <div className="flex items-end gap-3">
            <div className="w-40">
              <label className="label" htmlFor="relation">Parentesco</label>
              <select id="relation" className="input" value={relation}
                onChange={(e) => setRelation(e.target.value)}>
                {RELATIONS.map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>
            <button className="btn-primary" disabled={saving || (mode === "existing" && !selected)}>
              {saving ? "Guardando..." : "Agregar acudiente"}
            </button>
          </div>
        </form>
        {error && <p className="error mt-3">{error}</p>}
      </div>

      <div className="card">
        <h2 className="mb-3 font-semibold">Deportistas a su cargo</h2>
        {dependents.length === 0 ? (
          <p className="text-sm text-slate-500">No es acudiente de ningun deportista.</p>
        ) : (
          <ul className="divide-y divide-slate-100 text-sm">
            {dependents.map(({ relation: rel, person: d }) => (
              <li key={d.id} className="py-2">
                <Link href={`/dashboard/people/${d.id}`} className="text-brand-700 hover:underline">
                  {fullName(d)}
                </Link>{" "}
                <span className="text-slate-500">
                  · {rel}{d.age !== null ? ` · ${d.age} anos` : ""}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
