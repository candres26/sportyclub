"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

const nav = [
  { href: "/platform", label: "Resumen" },
  { href: "/platform/clubs", label: "Clubes" },
  { href: "/platform/admins", label: "Administradores" },
];

export default function PlatformShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();

  async function logout() {
    await fetch("/api/platform/auth/logout", { method: "POST" });
    router.push("/platform/login");
    router.refresh();
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-lg font-semibold text-brand-700">SportyClub</p>
            <p className="text-xs text-slate-500">Plataforma</p>
          </div>
          <button className="btn-ghost" onClick={logout}>
            Salir
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-6 py-6">
        <nav className="mb-6 flex gap-2">
          {nav.map((item) => {
            const active = pathname === item.href;
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
