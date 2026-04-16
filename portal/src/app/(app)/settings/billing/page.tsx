"use client";

import { useAuth } from "@/stores/auth-store";
import { useTenantDetail } from "@/hooks/useTenants";
import { usePlanDetail } from "@/hooks/usePlans";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Badge from "@/components/ui/badge/Badge";
import { formatNumber } from "@/lib/format";

export default function BillingSettingsPage() {
  const { user } = useAuth();
  const tenantId = user?.tenant_id || "";

  const { data: tenant, isLoading: tenantLoading } = useTenantDetail(tenantId);
  const { data: plan, isLoading: planLoading } = usePlanDetail(tenant?.plan_id || "");

  if (tenantLoading || planLoading) {
    return (
      <div>
        <PageBreadcrumb pageTitle="Billing" />
        <div className="h-64 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse" />
      </div>
    );
  }

  return (
    <div>
      <PageBreadcrumb pageTitle="Billing" />

      <div className="space-y-6">
        <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
          <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
            <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Current Plan</h3>
          </div>
          <div className="p-4 sm:p-6">
            <div className="flex items-center gap-3 mb-6">
              <h4 className="text-xl font-semibold text-gray-800 dark:text-white/90">{plan?.name || "No Plan"}</h4>
              <Badge variant="light" color="success">Active</Badge>
            </div>
            {plan && (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-xl bg-gray-50 dark:bg-gray-900 p-4">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Max Terminals</p>
                  <p className="text-lg font-semibold text-gray-800 dark:text-white/90 mt-1">{formatNumber(plan.max_terminals)}</p>
                </div>
                <div className="rounded-xl bg-gray-50 dark:bg-gray-900 p-4">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Max Users</p>
                  <p className="text-lg font-semibold text-gray-800 dark:text-white/90 mt-1">{formatNumber(plan.max_users)}</p>
                </div>
                <div className="rounded-xl bg-gray-50 dark:bg-gray-900 p-4">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Slots / Day</p>
                  <p className="text-lg font-semibold text-gray-800 dark:text-white/90 mt-1">{formatNumber(plan.max_slots_per_day)}</p>
                </div>
                <div className="rounded-xl bg-gray-50 dark:bg-gray-900 p-4">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Retention</p>
                  <p className="text-lg font-semibold text-gray-800 dark:text-white/90 mt-1">{plan.retention_days} days</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {plan && (
          <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
            <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
              <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Plan Features</h3>
            </div>
            <div className="p-4 sm:p-6">
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                <div className="flex items-center gap-2 text-sm">
                  {plan.allowed_ai_providers.length > 0 ? (
                    <svg className="h-5 w-5 text-success-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  ) : (
                    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                  )}
                  <span className="text-gray-700 dark:text-gray-300">AI Providers: {plan.allowed_ai_providers.join(", ") || "None"}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  {plan.custom_prompt_allowed ? (
                    <svg className="h-5 w-5 text-success-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  ) : (
                    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                  )}
                  <span className="text-gray-700 dark:text-gray-300">Custom Prompts</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  {plan.report_export_allowed ? (
                    <svg className="h-5 w-5 text-success-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  ) : (
                    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                  )}
                  <span className="text-gray-700 dark:text-gray-300">Report Export</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <svg className="h-5 w-5 text-success-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  <span className="text-gray-700 dark:text-gray-300">API Rate Limit: {plan.api_rate_limit_per_min}/min</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
