"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/client";
import type { Me } from "@/lib/types";

const nav = [
  { href: "/dashboard", label: "Inicio" },
  { href: "/dashboard/people", label: "Deportistas" },
  { href: "/dashboard/users", label: "Usuarios" },
  { href: "/dashboard/roles", label: "Roles" },
  { href: "/dashboard/invitations", label: "Invitaciones" },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    apiFetch<Me>("auth/me")
      .then(setMe)
      .catch(() => router.push("/login"));
  }, [router]);

  async function logout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-lg font-semibold text-brand-700">SportyClub</p>
            <p className="text-xs text-slate-500">{me?.tenant.name ?? "..."}</p>
          </div>
          <div className="flex items-center gap-4">
            <span className="hidden text-sm text-slate-500 sm:block">{me?.email}</span>
            <button className="btn-ghost" onClick={logout}>
              Salir
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-6 py-6">
        <nav className="mb-6 flex gap-2">
          {nav.map((item) => {
            const active =
              item.href === "/dashboard"
                ? pathname === item.href
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-lg px-3 py-1.5 text-sm ${
                  active
                    ? "bg-brand-600 text-white"
                    : "bg-white text-slate-600 hover:bg-slate-100"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        {children}
      </div>
    </div>
  );
}
