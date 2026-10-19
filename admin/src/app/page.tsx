import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import {
  PLATFORM_ACCESS_COOKIE,
  PLATFORM_REFRESH_COOKIE,
} from "@/lib/platform-session";

export default async function Home() {
  const store = await cookies();
  const hasPlatformSession =
    store.get(PLATFORM_ACCESS_COOKIE) || store.get(PLATFORM_REFRESH_COOKIE);

  redirect(hasPlatformSession ? "/platform" : "/dashboard");
}
