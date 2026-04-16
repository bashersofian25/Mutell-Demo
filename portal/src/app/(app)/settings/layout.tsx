"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const settingsNav = [
  { href: "/settings/organization", label: "Organization" },
  { href: "/settings/ai", label: "AI Configuration" },
  { href: "/settings/notifications", label: "Notifications" },
  { href: "/settings/billing", label: "Billing" },
  { href: "/settings/security", label: "Security" },
];

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
      <div className="lg:col-span-1">
        <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
          <div className="p-4">
            <nav className="flex flex-col gap-1">
              {settingsNav.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    pathname === item.href
                      ? "bg-brand-50 text-brand-500 dark:bg-brand-500/[0.12] dark:text-brand-400"
                      : "text-gray-500 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-white/[0.03]"
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </div>
      </div>
      <div className="lg:col-span-3">{children}</div>
    </div>
  );
}
