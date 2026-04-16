"use client";

import { useAdminHealth } from "@/hooks/useAdmin";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import StatusBadge from "@/components/common/StatusBadge";

export default function HealthPage() {
  const { data, isLoading } = useAdminHealth();

  const health = data?.data;

  const statusColor = (s: string) =>
    s === "connected" || s === "healthy" || s === "ok"
      ? "success"
      : s === "degraded" || s === "unknown"
        ? "warning"
        : "error";

  const services = health
    ? [
        { name: "Database", status: health.database, icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" /></svg> },
        { name: "Cache (Redis)", status: health.redis, icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a4.5 4.5 0 01.9-2.7L5.737 5.1a3.375 3.375 0 012.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 01.9 2.7m0 0a3 3 0 01-3 3m0 3h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008zm-3 6h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008z" /></svg> },
        { name: "Celery Workers", status: health.workers, icon: <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a4.5 4.5 0 01.9-2.7L5.737 5.1a3.375 3.375 0 012.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 01.9 2.7m0 0a3 3 0 01-3 3m0 3h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008zm-3 6h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008z" /></svg> },
      ]
    : [];

  return (
    <div>
      <PageBreadcrumb pageTitle="System Health" />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {isLoading ? (
          [1, 2, 3].map((i) => <div key={i} className="h-28 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse" />)
        ) : (
          services.map((service) => (
            <div key={service.name} className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03]">
              <div className="flex items-center gap-4">
                <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${
                  statusColor(service.status) === "success" ? "bg-success-50 dark:bg-success-500/15 text-success-500" :
                  statusColor(service.status) === "warning" ? "bg-warning-50 dark:bg-warning-500/15 text-warning-500" :
                  "bg-error-50 dark:bg-error-500/15 text-error-500"
                }`}>
                  {service.icon}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-800 dark:text-white/90">{service.name}</p>
                  <div className="mt-1">
                    <StatusBadge status={service.status === "connected" ? "active" : service.status === "unknown" ? "pending" : service.status} />
                  </div>
                </div>
                <div className={`h-3 w-3 rounded-full ${
                  statusColor(service.status) === "success" ? "bg-success-500 animate-pulse" :
                  statusColor(service.status) === "warning" ? "bg-warning-500" :
                  "bg-error-500"
                }`} />
              </div>
            </div>
          ))
        )}
      </div>

      <div className="mt-6 text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        Auto-refreshes every 10 seconds
      </div>
    </div>
  );
}
