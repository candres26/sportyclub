import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import {
  PLATFORM_ACCESS_COOKIE,
  PLATFORM_REFRESH_COOKIE,
} from "@/lib/platform-session";

import PlatformShell from "../platform-shell";

export default async function PlatformPanelLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const store = await cookies();
  const hasSession =
    store.get(PLATFORM_ACCESS_COOKIE) || store.get(PLATFORM_REFRESH_COOKIE);

  if (!hasSession) redirect("/platform/login");

  return <PlatformShell>{children}</PlatformShell>;
}
