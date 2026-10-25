"use client";

import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "@/lib/client";
import { formatDate } from "@/lib/people";
import type { AthleteProfile, Measurement, Metric, Person } from "@/lib/types";

const PROFILE_FIELDS = [
  { key: "blood_type", label: "Grupo sanguineo (RH)" },
  { key: "insurance", label: "EPS / seguro" },
  { key: "dominant_side", label: "Lateralidad (diestro/zurdo)" },
  { key: "allergies", label: "Alergias" },
  { key: "medical_notes", label: "Observaciones medicas" },
] as const;

type ProfileKey = (typeof PROFILE_FIELDS)[number]["key"];
type ProfileForm = Record<ProfileKey, string>;

function today(): string {
  return new Date().toLocaleDateString("en-CA");
}

export default function SheetTab({ person }: { person: Person }) {
  const [profile, setProfile] = useState<ProfileForm | null>(null);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [history, setHistory] = useState<Measurement[]>([]);
  const [measure, setMeasure] = useState({ metric_id: "", value: "", measured_at: today() });
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [p, m, h] = await Promise.all([
        apiFetch<AthleteProfile>(`people/${person.id}/profile`),
        apiFetch<Metric[]>("metrics"),
        apiFetch<Measurement[]>(`people/${person.id}/measurements`),
      ]);
      setProfile(
        Object.fromEntries(PROFILE_FIELDS.map(({ key }) => [key, p[key] ?? ""])) as ProfileForm,
      );
      setMetrics(m);
      setHistory(h);
      setMeasure((cur) => (cur.metric_id || m.length === 0 ? cur : { ...cur, metric_id: m[0].id }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar");
    }
  }, [person.id]);

  useEffect(() => {
    load();
  }, [load]);

  async function saveProfile(event: React.FormEvent) {
    event.preventDefault();
    if (!profile) return;
    setError(null);
    setNotice(null);
    try {
      await apiFetch(`people/${person.id}/profile`, {
        method: "PUT",
        body: JSON.stringify(profile),
      });
      setNotice("Ficha guardada");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    }
  }

  async function addMeasurement(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    try {
      await apiFetch(`people/${person.id}/measurements`, {
        method: "POST",
        body: JSON.stringify(measure),
      });
      setMeasure({ ...measure, value: "" });
      setHistory(await apiFetch<Measurement[]>(`people/${person.id}/measurements`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al registrar");
    }
  }

  async function removeMeasurement(id: string) {
    if (!confirm("Eliminar esta medicion?")) return;
    try {
      await apiFetch(`people/${person.id}/measurements/${id}`, { method: "DELETE" });
      setHistory((h) => h.filter((m) => m.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al eliminar");
    }
  }

  // Ultimo valor de cada metrica (el historial llega ordenado del mas reciente al mas antiguo).
  const latest = new Map<string, Measurement>();
  for (const m of history) if (!latest.has(m.metric_id)) latest.set(m.metric_id, m);

  return (
    <div className="space-y-4">
      {error && <p className="error">{error}</p>}
      {notice && <p className="text-sm text-green-700">{notice}</p>}

      <div className="card">
        <h2 className="mb-3 font-semibold">Medidas actuales</h2>
        {latest.size === 0 ? (
          <p className="text-sm text-slate-500">Sin mediciones registradas.</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-3">
            {[...latest.values()].map((m) => (
              <div key={m.metric_id} className="rounded-lg bg-slate-50 p-3">
                <p className="text-xs text-slate-500">{m.metric_name}</p>
                <p className="text-lg font-semibold">
                  {Number(m.value)} {m.unit}
                </p>
                <p className="text-xs text-slate-400">{formatDate(m.measured_at)}</p>
              </div>
            ))}
          </div>
        )}

        <form onSubmit={addMeasurement} className="mt-4 flex flex-col gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:items-end">
          <div className="sm:w-44">
            <label className="label" htmlFor="metric">Medida</label>
            <select id="metric" className="input" value={measure.metric_id}
              onChange={(e) => setMeasure({ ...measure, metric_id: e.target.value })}>
              {metrics.map((m) => (
                <option key={m.id} value={m.id}>{m.name} ({m.unit})</option>
              ))}
            </select>
          </div>
          <div className="sm:w-32">
            <label className="label" htmlFor="value">Valor</label>
            <input id="value" type="number" step="0.01" min="0" className="input" required
              value={measure.value} onChange={(e) => setMeasure({ ...measure, value: e.target.value })} />
          </div>
          <div className="sm:w-44">
            <label className="label" htmlFor="measured_at">Fecha</label>
            <input id="measured_at" type="date" className="input" required
              value={measure.measured_at}
              onChange={(e) => setMeasure({ ...measure, measured_at: e.target.value })} />
          </div>
          <button className="btn-primary" disabled={!measure.metric_id}>Registrar</button>
        </form>
      </div>

      <div className="card">
        <h2 className="mb-3 font-semibold">Historial</h2>
        {history.length === 0 ? (
          <p className="text-sm text-slate-500">Sin historial.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-400">
              <tr>
                <th className="py-2">Fecha</th>
                <th className="py-2">Medida</th>
                <th className="py-2">Valor</th>
                <th className="py-2"></th>
              </tr>
            </thead>
            <tbody>
              {history.map((m) => (
                <tr key={m.id} className="border-t border-slate-100">
                  <td className="py-2">{formatDate(m.measured_at)}</td>
                  <td className="py-2 text-slate-500">{m.metric_name}</td>
                  <td className="py-2">{Number(m.value)} {m.unit}</td>
                  <td className="py-2 text-right">
                    <button className="text-xs text-red-600 hover:underline"
                      onClick={() => removeMeasurement(m.id)}>
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {profile && (
        <form onSubmit={saveProfile} className="card grid gap-3 sm:grid-cols-2">
          <h2 className="font-semibold sm:col-span-2">Datos medicos y deportivos</h2>
          {PROFILE_FIELDS.map(({ key, label }) => (
            <div key={key} className={key === "allergies" || key === "medical_notes" ? "sm:col-span-2" : undefined}>
              <label className="label" htmlFor={key}>{label}</label>
              {key === "allergies" || key === "medical_notes" ? (
                <textarea id={key} rows={2} className="input" value={profile[key]}
                  onChange={(e) => setProfile({ ...profile, [key]: e.target.value })} />
              ) : (
                <input id={key} className="input" value={profile[key]}
                  maxLength={key === "blood_type" ? 5 : undefined}
                  onChange={(e) => setProfile({ ...profile, [key]: e.target.value })} />
              )}
            </div>
          ))}
          <div className="sm:col-span-2">
            <button className="btn-primary">Guardar ficha</button>
          </div>
        </form>
      )}
    </div>
  );
}
