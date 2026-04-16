"use client";

import { useState } from "react";
import Input from "@/components/form/input/InputField";
import DatePicker from "@/components/form/date-picker";
import { useAdminAuditLog } from "@/hooks/useAdmin";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Pagination from "@/components/tables/Pagination";
import EmptyState from "@/components/common/EmptyState";
import { truncate } from "@/lib/format";

export default function AuditLogPage() {
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const perPage = 20;

  const { data, isLoading } = useAdminAuditLog({
    page,
    per_page: perPage,
    action: actionFilter || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
  });

  const entries = data?.items || [];
  const total = data?.total || 0;

  const clearFilters = () => {
    setActionFilter("");
    setDateFrom("");
    setDateTo("");
    setPage(1);
  };

  const hasFilters = actionFilter || dateFrom || dateTo;

  return (
    <div>
      <PageBreadcrumb pageTitle="Audit Log" />

      <div className="mb-6 flex flex-wrap items-end gap-3">
        <div className="w-64">
          <Input
            placeholder="Filter by action..."
            value={actionFilter}
            onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
          />
        </div>
        <div className="w-48">
          <DatePicker
            id="audit-date-from"
            placeholder="Date from"
            onChange={([date]: Date[]) => { if (date) setDateFrom(date.toISOString()); setPage(1); }}
          />
        </div>
        <div className="w-48">
          <DatePicker
            id="audit-date-to"
            placeholder="Date to"
            onChange={([date]: Date[]) => { if (date) setDateTo(date.toISOString()); setPage(1); }}
          />
        </div>
        {hasFilters && (
          <button onClick={clearFilters} className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300">
            Clear filters
          </button>
        )}
      </div>

      <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
        <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90">{`Activity Log${data ? ` (${data.total})` : ""}`}</h3>
        </div>
        <div className="max-w-full overflow-x-auto">
          {isLoading ? (
            <div className="p-6 space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-12 rounded-lg bg-gray-100 dark:bg-gray-800 animate-pulse" />)}</div>
          ) : !entries.length ? (
            <EmptyState title="No audit entries" description="No log entries match your filter." />
          ) : (
              <table className="min-w-full">
                <thead className="border-b border-gray-100 dark:border-white/[0.05]">
                  <tr>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Action</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Resource</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">User ID</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">IP</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Status</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-white/[0.05]">
                  {entries.map((entry) => (
                    <tr key={entry.id} className="hover:bg-gray-50 dark:hover:bg-white/[0.03] transition-colors duration-150">
                      <td className="px-5 py-4 text-sm font-medium text-gray-800 dark:text-white/90 font-mono">{entry.action}</td>
                      <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400">
                        {entry.resource_type ? `${entry.resource_type}/${truncate(entry.resource_id || "", 8)}` : "—"}
                      </td>
                      <td className="px-5 py-4 text-xs font-mono text-gray-500 dark:text-gray-400">{truncate(entry.user_id || "", 8)}</td>
                      <td className="px-5 py-4 text-xs font-mono text-gray-500 dark:text-gray-400">{entry.ip_address || "—"}</td>
                      <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400">{entry.status_code || "—"}</td>
                      <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400">{new Date(entry.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
          )}
        </div>
        {total > perPage && (
          <div className="px-6 py-4 border-t border-gray-100 dark:border-gray-800">
            <Pagination currentPage={page} totalPages={Math.ceil(total / perPage)} onPageChange={setPage} />
          </div>
        )}
      </div>
    </div>
  );
}
