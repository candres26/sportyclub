import Link from "next/link";

import {
  PLANS,
  TRUSTED_CLUBS,
  WHATSAPP_MESSAGE,
  WHATSAPP_NUMBER,
  type Plan,
} from "@/lib/landing-content";

const IS_DEV = process.env.NODE_ENV !== "production";

const whatsappUrl = WHATSAPP_NUMBER
  ? `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(WHATSAPP_MESSAGE)}`
  : null;

const FEATURES: { title: string; text: string; soon?: boolean }[] = [
  {
    title: "Deportistas y acudientes",
    text: "Registra a cada deportista con sus datos y vincula a sus padres o tutores. Un mismo acudiente puede tener varios hijos en el club, y también entrenar.",
  },
  {
    title: "Ficha técnica con historial",
    text: "Estatura, peso, alcance y las medidas que tu disciplina necesite. Cada medición queda guardada con su fecha para ver la evolución.",
  },
  {
    title: "Roles para tu equipo",
    text: "El dueño tiene el control total, la administración gestiona el día a día y los entrenadores ven a sus deportistas y actualizan la ficha técnica.",
  },
  {
    title: "Datos aislados y seguros",
    text: "Cada club tiene su propio espacio. La información de tus deportistas solo la ve tu club, con aislamiento a nivel de base de datos.",
  },
  {
    title: "Membresías y mensualidades",
    text: "Planes por disciplina, mensualidades con fecha de pago y recargo por mora configurable, y estado de cuenta por acudiente.",
    soon: true,
  },
  {
    title: "Varias disciplinas",
    text: "Empieza con un deporte y suma otros cuando tu club crezca, cada uno con sus planes y sus métricas.",
  },
];

function WhatsAppButton({ className = "", label }: { className?: string; label: string }) {
  if (!whatsappUrl) return null;
  return (
    <a
      href={whatsappUrl}
      target="_blank"
      rel="noopener noreferrer"
      className={`inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-500 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-600 ${className}`}
    >
      <svg aria-hidden viewBox="0 0 24 24" className="h-5 w-5 fill-current">
        <path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.2.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.7 11.9 11.9 0 0 0 4.6 4c1.7.7 2.4.8 3.2.7.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.1-.3-.2-.5-.3Z" />
      </svg>
      {label}
    </a>
  );
}

function ConfigHint({ children }: { children: React.ReactNode }) {
  if (!IS_DEV) return null;
  return (
    <p className="mx-auto max-w-xl rounded-lg border border-dashed border-amber-400 bg-amber-50 px-4 py-3 text-center text-sm text-amber-800">
      <strong>Solo visible en desarrollo:</strong> {children}
    </p>
  );
}

function ProductPreview() {
  const rows = [
    { metric: "Estatura", value: "152,5 cm", delta: "+3,5" },
    { metric: "Peso", value: "41,0 kg", delta: "+1,2" },
    { metric: "Alcance", value: "149,0 cm", delta: "+2,0" },
  ];
  return (
    <div aria-hidden className="relative mx-auto w-full max-w-md">
      <div className="absolute -inset-4 rounded-3xl bg-gradient-to-tr from-brand-500/20 to-emerald-400/20 blur-2xl" />
      <div className="relative rounded-2xl border border-slate-200 bg-white p-5 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-100 font-semibold text-brand-700">
            SR
          </div>
          <div>
            <p className="font-semibold">Sofía Ruiz</p>
            <p className="text-xs text-slate-500">13 años · Acudiente: Carlos Ruiz (padre)</p>
          </div>
          <span className="ml-auto rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
            Activa
          </span>
        </div>
        <p className="mt-5 text-xs font-medium uppercase tracking-wide text-slate-400">
          Ficha técnica
        </p>
        <div className="mt-2 grid grid-cols-3 gap-2">
          {rows.map((r) => (
            <div key={r.metric} className="rounded-xl bg-slate-50 p-3">
              <p className="text-xs text-slate-500">{r.metric}</p>
              <p className="mt-1 text-sm font-semibold">{r.value}</p>
              <p className="text-xs text-emerald-600">{r.delta} en 6 meses</p>
            </div>
          ))}
        </div>
        <div className="mt-4 flex h-16 items-end gap-1.5">
          {[22, 34, 41, 52, 60, 71, 82, 95].map((h, i) => (
            <div
              key={i}
              className="flex-1 rounded-t bg-brand-500/80"
              style={{ height: `${h}%` }}
            />
          ))}
        </div>
        <p className="mt-1 text-right text-[11px] text-slate-400">Evolución de estatura</p>
      </div>
    </div>
  );
}

function ClubsCarousel() {
  if (TRUSTED_CLUBS.length === 0) {
    return (
      <section className="px-6 py-10">
        <ConfigHint>
          agrega los clubes y sus logos en <code>TRUSTED_CLUBS</code> de{" "}
          <code>src/lib/landing-content.ts</code> para mostrar el carrusel.
        </ConfigHint>
      </section>
    );
  }
  // La lista se duplica para que la animacion sea continua (se desplaza el 50 %).
  const items = [...TRUSTED_CLUBS, ...TRUSTED_CLUBS];
  return (
    <section className="border-y border-slate-200 bg-white py-10">
      <p className="text-center text-sm font-medium text-slate-500">
        Clubes que confían en SportyClub
      </p>
      <div className="group relative mt-6 overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_10%,black_90%,transparent)]">
        <ul className="flex w-max animate-marquee items-center gap-14 group-hover:[animation-play-state:paused] motion-reduce:animate-none">
          {items.map((club, i) => (
            <li key={`${club.name}-${i}`} aria-hidden={i >= TRUSTED_CLUBS.length}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={club.logo}
                alt={club.name}
                className="h-12 w-auto max-w-[140px] object-contain opacity-70 grayscale transition hover:opacity-100 hover:grayscale-0"
              />
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function PlanCard({ plan }: { plan: Plan }) {
  return (
    <div
      className={`relative flex flex-col rounded-2xl border bg-white p-6 ${
        plan.highlighted ? "border-brand-500 shadow-lg ring-1 ring-brand-500" : "border-slate-200"
      }`}
    >
      {plan.highlighted && (
        <span className="absolute -top-3 left-6 rounded-full bg-brand-600 px-2.5 py-0.5 text-xs font-medium text-white">
          Recomendado
        </span>
      )}
      <h3 className="text-lg font-semibold">{plan.name}</h3>
      <p className="mt-1 text-sm text-slate-500">{plan.description}</p>
      <p className="mt-5">
        <span className="text-3xl font-bold tracking-tight">{plan.price}</span>{" "}
        <span className="text-sm text-slate-500">{plan.period}</span>
      </p>
      <ul className="mt-5 flex-1 space-y-2 text-sm">
        {plan.features.map((f) => (
          <li key={f} className="flex gap-2">
            <span className="text-emerald-600">✓</span>
            {f}
          </li>
        ))}
      </ul>
      <WhatsAppButton label="Quiero este plan" className="mt-6 w-full" />
    </div>
  );
}

function Pricing() {
  if (PLANS.length === 0) {
    return (
      <section id="precios" className="px-6 py-10">
        <ConfigHint>
          agrega tus planes en <code>PLANS</code> de <code>src/lib/landing-content.ts</code> para
          mostrar la sección de precios.
        </ConfigHint>
      </section>
    );
  }
  return (
    <section id="precios" className="px-6 py-20">
      <div className="mx-auto max-w-5xl">
        <h2 className="text-center text-3xl font-bold tracking-tight">Precios</h2>
        <p className="mx-auto mt-3 max-w-xl text-center text-slate-600">
          Elige el plan que se ajusta al tamaño de tu club.
        </p>
        <div
          className={`mt-10 grid gap-6 ${
            PLANS.length >= 3 ? "md:grid-cols-3" : PLANS.length === 2 ? "md:grid-cols-2" : ""
          }`}
        >
          {PLANS.map((plan) => (
            <PlanCard key={plan.name} plan={plan} />
          ))}
        </div>
      </div>
    </section>
  );
}

export default function Landing() {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-10 border-b border-slate-200/70 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <span className="text-lg font-bold text-brand-700">SportyClub</span>
          <nav className="flex items-center gap-5 text-sm text-slate-600">
            <a href="#funcionalidades" className="hidden hover:text-slate-900 sm:block">
              Funcionalidades
            </a>
            {PLANS.length > 0 && (
              <a href="#precios" className="hidden hover:text-slate-900 sm:block">
                Precios
              </a>
            )}
            {whatsappUrl && (
              <a
                href={whatsappUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-lg bg-brand-600 px-3 py-1.5 font-medium text-white hover:bg-brand-700"
              >
                Contáctanos
              </a>
            )}
          </nav>
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden px-6 pb-20 pt-16 sm:pt-24">
          <div className="pointer-events-none absolute inset-x-0 top-0 -z-0 h-[480px] bg-gradient-to-b from-brand-50 to-transparent" />
          <div className="relative mx-auto grid max-w-6xl items-center gap-14 lg:grid-cols-2">
            <div>
              <p className="inline-block rounded-full bg-white px-3 py-1 text-xs font-medium text-brand-700 ring-1 ring-brand-100">
                Software para clubes deportivos
              </p>
              <h1 className="mt-5 text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
                Tu club, tus deportistas y sus familias en un solo lugar
              </h1>
              <p className="mt-5 max-w-lg text-lg text-slate-600">
                Registra deportistas y acudientes, lleva su ficha técnica con historial y organiza
                a tu equipo de trabajo. Menos planillas, más tiempo para entrenar.
              </p>
              <div className="mt-8 flex flex-wrap items-center gap-3">
                <WhatsAppButton label="Escríbenos por WhatsApp" />
                <a href="#funcionalidades" className="btn-ghost rounded-xl px-5 py-3">
                  Ver funcionalidades
                </a>
              </div>
              {!whatsappUrl && (
                <div className="mt-6">
                  <ConfigHint>
                    configura <code>WHATSAPP_NUMBER</code> en{" "}
                    <code>src/lib/landing-content.ts</code> para mostrar el botón de WhatsApp.
                  </ConfigHint>
                </div>
              )}
            </div>
            <ProductPreview />
          </div>
        </section>

        <ClubsCarousel />

        <section id="funcionalidades" className="px-6 py-20">
          <div className="mx-auto max-w-6xl">
            <h2 className="text-center text-3xl font-bold tracking-tight">
              Todo lo que tu club necesita
            </h2>
            <p className="mx-auto mt-3 max-w-xl text-center text-slate-600">
              Pensado para clubes con muchos deportistas menores de edad, donde los padres son
              parte del día a día.
            </p>
            <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {FEATURES.map((f) => (
                <div key={f.title} className="rounded-2xl border border-slate-200 bg-white p-6">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold">{f.title}</h3>
                    {f.soon && (
                      <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700">
                        Próximamente
                      </span>
                    )}
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-slate-600">{f.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <Pricing />

        {whatsappUrl && (
          <section className="px-6 pb-20">
            <div className="mx-auto max-w-4xl rounded-3xl bg-brand-700 px-8 py-12 text-center text-white">
              <h2 className="text-2xl font-bold sm:text-3xl">¿Listo para organizar tu club?</h2>
              <p className="mx-auto mt-3 max-w-lg text-brand-100">
                Cuéntanos de tu club y te ayudamos a empezar.
              </p>
              <WhatsAppButton label="Hablemos por WhatsApp" className="mt-7" />
            </div>
          </section>
        )}
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-6 py-6 text-sm text-slate-500 sm:flex-row">
          <p>© {new Date().getFullYear()} SportyClub</p>
          <Link href="/platform/login" className="hover:text-slate-700">
            Acceso administradores
          </Link>
        </div>
      </footer>
    </div>
  );
}
