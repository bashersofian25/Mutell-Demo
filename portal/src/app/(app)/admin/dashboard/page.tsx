"use client";

import { useAdminTenants, useAdminUsers, useAdminPlans, useAdminAIProviders } from "@/hooks/useAdmin";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import StatCard from "@/components/common/StatCard";
import { formatNumber } from "@/lib/format";

export default function AdminDashboardPage() {
  const { data: tenants } = useAdminTenants();
  const { data: users } = useAdminUsers();
  const { data: plans } = useAdminPlans();
  const { data: providers } = useAdminAIProviders();

  return (
    <div>
      <PageBreadcrumb pageTitle="Admin Dashboard" />

      <div className="mb-6">
        <h1 className="text-heading-6 font-bold text-gray-900 dark:text-white">Platform Administration</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Manage your platform, tenants, and configuration.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4 mb-6">
        <StatCard
          label="Total Tenants"
          value={tenants ? formatNumber(tenants.total) : "..."}
          icon={<svg className="h-6 w-6 text-brand-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>}
        />
        <StatCard
          label="Total Users"
          value={users ? formatNumber(users.total) : "..."}
          icon={<svg className="h-6 w-6 text-success-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" /></svg>}
        />
        <StatCard
          label="Plans"
          value={plans ? formatNumber(plans.total) : "..."}
          icon={<svg className="h-6 w-6 text-warning-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>}
        />
        <StatCard
          label="AI Providers"
          value={providers ? formatNumber(providers.length) : "..."}
          icon={<svg className="h-6 w-6 text-info-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3" /></svg>}
        />
      </div>

      <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
        <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
          <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Platform Overview</h3>
        </div>
        <div className="p-4 sm:p-6">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Use the sidebar to manage tenants, plans, AI providers, users, and system health.
          </p>
        </div>
      </div>
    </div>
  );
}
