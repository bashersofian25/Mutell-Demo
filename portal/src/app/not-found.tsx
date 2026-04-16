"use client";

import { useRouter } from "next/navigation";
import Button from "@/components/ui/button/Button";

export default function NotFound() {
  const router = useRouter();
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <div className="text-center">
        <div className="flex justify-center mb-4">
          <img
            src="/mutell-logo.svg"
            alt="Mutell logo"
            className="h-52 w-auto dark:invert"
            loading="lazy"
          />
        </div>
        <h1 className="text-title-xl font-bold text-gray-300 dark:text-gray-700 mb-4">404</h1>
        <h2 className="text-title-sm font-semibold text-gray-800 dark:text-white/90 mb-2">Page not found</h2>
        <p className="text-gray-500 dark:text-gray-400 mb-8 max-w-md mx-auto">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>
        <Button onClick={() => router.push("/dashboard")}>Go to Dashboard</Button>
      </div>
    </div>
  );
}
