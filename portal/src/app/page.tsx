"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/stores/auth-store";

export default function Home() {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    if (!user) {
      router.replace("/login");
    } else if (user.role === "super_admin") {
      router.replace("/admin/dashboard");
    } else {
      router.replace("/dashboard");
    }
  }, [isLoading, user, router]);

  return (
    <div className="flex h-screen items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-500" />
    </div>
  );
}
