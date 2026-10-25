"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiFetch } from "@/lib/client";
import { DOCUMENT_TYPES } from "@/lib/people";
import type { Person } from "@/lib/types";

const FIELDS = [
  "first_name",
  "last_name",
  "document_type",
  "document_number",
  "birth_date",
  "gender",
  "email",
  "phone",
  "address",
  "emergency_contact_name",
  "emergency_contact_phone",
  "notes",
] as const;

type Field = (typeof FIELDS)[number];
type FormState = Record<Field, string>;

function toForm(person: Person): FormState {
  return Object.fromEntries(FIELDS.map((f) => [f, person[f] ?? ""])) as FormState;
}

const LABELS: Record<Field, string> = {
  first_name: "Nombres",
  last_name: "Apellidos",
  document_type: "Tipo de documento",
  document_number: "Numero de documento",
  birth_date: "Fecha de nacimiento",
  gender: "Genero",
  email: "Correo",
  phone: "Telefono",
  address: "Direccion",
  emergency_contact_name: "Contacto de emergencia",
  emergency_contact_phone: "Telefono de emergencia",
  notes: "Observaciones",
};

export default function DataTab({
  person,
  onSaved,
}: {
  person: Person;
  onSaved: (person: Person) => void;
}) {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(() => toForm(person));
  const [isActive, setIsActive] = useState(person.is_active);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function onSave(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setSaving(true);
    try {
      // Los campos vacios se envian como null para poder borrarlos.
      const body = Object.fromEntries(
        FIELDS.map((f) => [f, form[f].trim() === "" ? null : form[f].trim()]),
      );
      const saved = await apiFetch<Person>(`people/${person.id}`, {
        method: "PATCH",
        body: JSON.stringify({ ...body, is_active: isActive }),
      });
      onSaved(saved);
      setNotice("Cambios guardados");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  }

  async function onDelete() {
    if (!confirm("Eliminar esta persona y toda su ficha? Esta accion no se puede deshacer.")) {
      return;
    }
    try {
      await apiFetch(`people/${person.id}`, { method: "DELETE" });
      router.push("/dashboard/people");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al eliminar");
    }
  }

  function input(field: Field) {
    if (field === "document_type") {
      return (
        <select id={field} className="input" value={form[field]}
          onChange={(e) => setForm({ ...form, [field]: e.target.value })}>
          <option value="">-</option>
          {DOCUMENT_TYPES.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>
      );
    }
    if (field === "notes") {
      return (
        <textarea id={field} className="input" rows={3} value={form[field]}
          onChange={(e) => setForm({ ...form, [field]: e.target.value })} />
      );
    }
    return (
      <input
        id={field}
        className="input"
        type={field === "birth_date" ? "date" : field === "email" ? "email" : "text"}
        required={field === "first_name" || field === "last_name"}
        value={form[field]}
        onChange={(e) => setForm({ ...form, [field]: e.target.value })}
      />
    );
  }

  return (
    <div className="card">
      <form onSubmit={onSave} className="grid gap-3 sm:grid-cols-2">
        {FIELDS.map((field) => (
          <div key={field} className={field === "notes" ? "sm:col-span-2" : undefined}>
            <label className="label" htmlFor={field}>{LABELS[field]}</label>
            {input(field)}
          </div>
        ))}
        <label className="flex items-center gap-2 text-sm sm:col-span-2">
          <input type="checkbox" checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)} />
          Activo en el club
        </label>
        <div className="flex items-center justify-between sm:col-span-2">
          <button className="btn-primary" disabled={saving}>
            {saving ? "Guardando..." : "Guardar cambios"}
          </button>
          <button type="button" className="text-sm text-red-600 hover:underline"
            onClick={onDelete}>
            Eliminar persona
          </button>
        </div>
      </form>
      {notice && <p className="mt-3 text-sm text-green-700">{notice}</p>}
      {error && <p className="error mt-3">{error}</p>}
    </div>
  );
}
