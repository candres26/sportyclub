import type { Metadata } from "next";
import { cookies, headers } from "next/headers";
import { redirect } from "next/navigation";

import { clubSlug } from "@/lib/host";
import {
  PLATFORM_ACCESS_COOKIE,
  PLATFORM_REFRESH_COOKIE,
} from "@/lib/platform-session";

import Landing from "./landing";

async function isRootDomain(): Promise<boolean> {
  const host = (await headers()).get("host") ?? "";
  return clubSlug(host) === null;
}

export async function generateMetadata(): Promise<Metadata> {
  if (!(await isRootDomain())) return {};
  return {
    title: "SportyClub - Software para clubes deportivos",
    description:
      "Gestiona deportistas, acudientes y la ficha tecnica de tu club deportivo en un solo lugar.",
  };
}

export default async function Home() {
  // Dominio raiz: landing publica de la app.
  if (await isRootDomain()) return <Landing />;

  // Subdominio de un club: al panel del club.
  const store = await cookies();
  const hasPlatformSession =
    store.get(PLATFORM_ACCESS_COOKIE) || store.get(PLATFORM_REFRESH_COOKIE);

  redirect(hasPlatformSession ? "/platform" : "/dashboard");
}
