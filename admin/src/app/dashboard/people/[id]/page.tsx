"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "@/lib/client";
import { fullName } from "@/lib/people";
import type { Person } from "@/lib/types";

import DataTab from "./data-tab";
import GuardiansTab from "./guardians-tab";
import SheetTab from "./sheet-tab";

const TABS = [
  { key: "data", label: "Datos" },
  { key: "guardians", label: "Responsables" },
  { key: "sheet", label: "Ficha tecnica" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

export default function PersonPage() {
  const { id } = useParams<{ id: string }>();
  const [person, setPerson] = useState<Person | null>(null);
  const [tab, setTab] = useState<TabKey>("data");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setPerson(await apiFetch<Person>(`people/${id}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar");
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  if (error && !person) {
    return (
      <div className="card">
        <p className="error">{error}</p>
        <Link href="/dashboard/people" className="mt-3 inline-block text-sm text-brand-700">
          Volver al listado
        </Link>
      </div>
    );
  }
  if (!person) return <p className="text-sm text-slate-500">Cargando...</p>;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <Link href="/dashboard/people" className="text-xs text-slate-500 hover:underline">
            ← Deportistas y acudientes
          </Link>
          <h1 className="text-xl font-semibold">{fullName(person)}</h1>
          <p className="text-sm text-slate-500">
            {person.age !== null ? `${person.age} anos` : "Sin fecha de nacimiento"}
            {!person.is_active && " · inactivo"}
          </p>
        </div>
        <div className="flex gap-2">
          {TABS.map((item) => (
            <button
              key={item.key}
              onClick={() => setTab(item.key)}
              className={`rounded-lg px-3 py-1.5 text-sm ${
                tab === item.key
                  ? "bg-brand-600 text-white"
                  : "bg-white text-slate-600 hover:bg-slate-100"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {tab === "data" && <DataTab person={person} onSaved={setPerson} />}
      {tab === "guardians" && <GuardiansTab person={person} />}
      {tab === "sheet" && <SheetTab person={person} />}
    </div>
  );
}
