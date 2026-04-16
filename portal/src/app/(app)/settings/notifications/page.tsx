"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import { NotificationSettings } from "@/types/notification";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import ComponentCard from "@/components/common/ComponentCard";
import toast from "react-hot-toast";

const DEFAULT_SETTINGS: NotificationSettings = {
  email_evaluations: true,
  email_failures: true,
  email_reports: false,
  push_mentions: true,
  push_weekly_summary: false,
};

function Toggle({ enabled, onChange, label, description }: { enabled: boolean; onChange: (v: boolean) => void; label: string; description: string }) {
  return (
    <div className="flex items-center justify-between py-4">
      <div>
        <p className="text-sm font-medium text-gray-800 dark:text-white/90">{label}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
      </div>
      <button
        onClick={() => onChange(!enabled)}
        className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${enabled ? "bg-brand-500" : "bg-gray-200 dark:bg-gray-700"}`}
      >
        <span className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${enabled ? "translate-x-5" : "translate-x-0"}`} />
      </button>
    </div>
  );
}

export default function NotificationsSettingsPage() {
  const [settings, setSettings] = useState<NotificationSettings>(DEFAULT_SETTINGS);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api.get<NotificationSettings>("/settings/notifications")
      .then((r) => setSettings(r.data))
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  const updateSetting = useCallback(async (key: keyof NotificationSettings, value: boolean) => {
    const next = { ...settings, [key]: value };
    setSettings(next);
    try {
      await api.put("/settings/notifications", next);
    } catch {
      toast.error("Failed to save notification setting");
      setSettings(settings);
    }
  }, [settings]);

  if (isLoading) {
    return (
      <div>
        <PageBreadcrumb pageTitle="Notifications" />
        <div className="space-y-6">
          {[1, 2].map((i) => (
            <div key={i} className="rounded-2xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-white/[0.03]">
              <div className="space-y-4">{[1, 2, 3].map((j) => <div key={j} className="h-12 rounded bg-gray-100 dark:bg-gray-800 animate-pulse" />)}</div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageBreadcrumb pageTitle="Notifications" />

      <div className="space-y-6">
        <ComponentCard title="Email Notifications" desc="Configure which email notifications you receive.">
          <Toggle
            enabled={settings.email_evaluations}
            onChange={(v) => updateSetting("email_evaluations", v)}
            label="Evaluation Complete"
            description="Get notified when a slot evaluation finishes."
          />
          <Toggle
            enabled={settings.email_failures}
            onChange={(v) => updateSetting("email_failures", v)}
            label="Evaluation Failed"
            description="Get notified when a slot evaluation fails."
          />
          <Toggle
            enabled={settings.email_reports}
            onChange={(v) => updateSetting("email_reports", v)}
            label="Report Ready"
            description="Get notified when a generated report is ready for download."
          />
        </ComponentCard>

        <ComponentCard title="Push Notifications" desc="Stay informed about team activity.">
          <Toggle
            enabled={settings.push_mentions}
            onChange={(v) => updateSetting("push_mentions", v)}
            label="Mentions"
            description="Get notified when you are mentioned in notes or comments."
          />
          <Toggle
            enabled={settings.push_weekly_summary}
            onChange={(v) => updateSetting("push_weekly_summary", v)}
            label="Weekly Summary"
            description="Receive a weekly summary of evaluation activity."
          />
        </ComponentCard>
      </div>
    </div>
  );
}
