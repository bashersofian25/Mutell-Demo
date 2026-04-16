"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useIsSuperAdmin } from "@/lib/hooks";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const isSuperAdmin = useIsSuperAdmin();
  const router = useRouter();

  useEffect(() => {
    if (!isSuperAdmin) {
      router.replace("/dashboard");
    }
  }, [isSuperAdmin, router]);

  if (!isSuperAdmin) return null;

  return <>{children}</>;
}
