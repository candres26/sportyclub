"use client";

import { useEffect, useState } from "react";

import { platformFetch } from "@/lib/platform-client";
import type { Club, PlatformMe } from "@/lib/types";

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="card">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-3xl font-semibold text-brand-700">{value}</p>
    </div>
  );
}

export default function PlatformHome() {
  const [me, setMe] = useState<PlatformMe | null>(null);
  const [clubs, setClubs] = useState<Club[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    platformFetch<PlatformMe>("auth/me")
      .then(setMe)
      .catch(() => undefined);
    platformFetch<Club[]>("clubs")
      .then(setClubs)
      .catch((err) => setError(err instanceof Error ? err.message : "Error"));
  }, []);

  const active = clubs.filter((club) => club.is_active).length;

  return (
    <div className="space-y-6">
      <div className="card">
        <h1 className="text-lg font-semibold">
          Hola{me ? `, ${me.full_name}` : ""}
        </h1>
        <p className="text-sm text-slate-500">
          Administracion de la plataforma SportyClub
        </p>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label="Clubes" value={clubs.length} />
        <Stat label="Activos" value={active} />
        <Stat label="Suspendidos" value={clubs.length - active} />
      </div>
    </div>
  );
}
