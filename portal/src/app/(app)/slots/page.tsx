"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useSlotList, useBulkReEvaluate } from "@/hooks/useSlots";
import { useTerminalList } from "@/hooks/useTerminals";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Button from "@/components/ui/button/Button";
import StatusBadge from "@/components/common/StatusBadge";
import Pagination from "@/components/tables/Pagination";
import Select from "@/components/form/Select";
import EmptyState from "@/components/common/EmptyState";
import ConfirmDialog from "@/components/common/ConfirmDialog";
import { formatRelativeTime, formatDuration, truncate } from "@/lib/format";
import { useIsTenantAdmin } from "@/lib/hooks";
import TagBadge from "@/components/common/TagBadge";

const statusOptions = [
  { value: "", label: "All Statuses" },
  { value: "evaluated", label: "Evaluated" },
  { value: "accepted", label: "Accepted" },
  { value: "pending", label: "Pending" },
  { value: "processing", label: "Processing" },
  { value: "unclear", label: "Unclear" },
  { value: "failed", label: "Failed" },
];

export default function SlotsPage() {
  const router = useRouter();
  const isAdmin = useIsTenantAdmin();

  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<string>("");
  const [terminalId, setTerminalId] = useState<string>("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [bulkConfirm, setBulkConfirm] = useState(false);

  const perPage = 20;

  const { data, isLoading } = useSlotList({
    page,
    per_page: perPage,
    status: (status || undefined) as any,
    terminal_id: terminalId || undefined,
  });

  const { data: terminalsData } = useTerminalList({ per_page: 100 });

  const bulkReEvaluate = useBulkReEvaluate();

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (!data?.items) return;
    if (selected.size === data.items.length) setSelected(new Set());
    else setSelected(new Set(data.items.map((s) => s.id)));
  };

  const handleBulkReEvaluate = () => {
    bulkReEvaluate.mutate(
      { slot_ids: Array.from(selected) },
      { onSuccess: () => { setSelected(new Set()); setBulkConfirm(false); } }
    );
  };

  const terminalOptions = [
    { value: "", label: "All Terminals" },
    ...(terminalsData?.items?.map((t) => ({ value: t.id, label: t.name })) || []),
  ];

  return (
    <div>
      <PageBreadcrumb pageTitle="Slots" />

      <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
        <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90">Evaluation Sessions{data ? ` (${data.total})` : ""}</h3>
          {isAdmin && selected.size > 0 && (
            <Button size="sm" onClick={() => setBulkConfirm(true)}>
              Re-evaluate ({selected.size})
            </Button>
          )}
        </div>

        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex flex-wrap items-center gap-3">
          <div className="w-44">
            <Select options={statusOptions} placeholder="Status" onChange={(v) => { setStatus(v); setPage(1); }} defaultValue={status} />
          </div>
          <div className="w-52">
            <Select options={terminalOptions} placeholder="Terminal" onChange={(v) => { setTerminalId(v); setPage(1); }} defaultValue={terminalId} />
          </div>
        </div>

        <div className="max-w-full overflow-x-auto">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-14 rounded-lg bg-gray-100 dark:bg-gray-800 animate-pulse" />
              ))}
            </div>
          ) : !data?.items?.length ? (
            <EmptyState
              icon={<svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>}
              title="No slots found"
              description="No evaluation sessions match your current filters."
            />
          ) : (
            <table className="min-w-full">
                <thead className="border-b border-gray-100 dark:border-white/[0.05]">
                  <tr>
                    {isAdmin && (
                      <th className="px-5 py-3 text-left">
                        <input type="checkbox" checked={data.items.length > 0 && selected.size === data.items.length} onChange={toggleAll} className="h-4 w-4 rounded border-gray-300" />
                      </th>
                    )}
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">ID</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Status</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Score</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Tags</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Duration</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Words</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-white/[0.05]">
                  {data.items.map((slot) => (
                    <tr
                      key={slot.id}
                      className="cursor-pointer hover:bg-gray-50 dark:hover:bg-white/[0.03] transition-colors"
                      onClick={() => router.push(`/slots/${slot.id}`)}
                    >
                      {isAdmin && (
                        <td className="px-5 py-4" onClick={(e) => e.stopPropagation()}>
                          <input type="checkbox" checked={selected.has(slot.id)} onChange={() => toggleSelect(slot.id)} className="h-4 w-4 rounded border-gray-300" />
                        </td>
                      )}
                      <td className="px-5 py-4 text-sm font-medium text-gray-800 dark:text-white/90">{truncate(slot.id, 8)}</td>
                      <td className="px-5 py-4 text-sm"><StatusBadge status={slot.status} /></td>
                      <td className="px-5 py-4 text-sm font-medium">
                        {slot.score_overall != null ? (
                          <span className={
                            slot.score_overall >= 80 ? "text-green-600 dark:text-green-400" :
                            slot.score_overall >= 60 ? "text-yellow-600 dark:text-yellow-400" :
                            slot.score_overall >= 40 ? "text-orange-600 dark:text-orange-400" :
                            "text-red-600 dark:text-red-400"
                          }>
                            {slot.score_overall.toFixed(1)}
                          </span>
                        ) : <span className="text-gray-400">—</span>}
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex flex-wrap gap-1">
                          {(slot.tags || []).map((tag) => (
                            <TagBadge key={tag} tag={tag} />
                          ))}
                        </div>
                      </td>
                      <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400">{formatDuration(slot.duration_secs)}</td>
                      <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400">{slot.word_count ?? "—"}</td>
                      <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400">{formatRelativeTime(slot.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
           )}
        </div>

        {data && data.total > perPage && (
          <div className="px-6 py-4 border-t border-gray-100 dark:border-gray-800">
            <Pagination currentPage={page} totalPages={Math.ceil(data.total / perPage)} onPageChange={setPage} />
          </div>
        )}
      </div>

      <ConfirmDialog
        isOpen={bulkConfirm}
        onClose={() => setBulkConfirm(false)}
        onConfirm={handleBulkReEvaluate}
        title="Bulk Re-evaluate"
        message={`Are you sure you want to re-evaluate ${selected.size} selected slots?`}
        confirmLabel="Re-evaluate"
        variant="primary"
        isLoading={bulkReEvaluate.isPending}
      />
    </div>
  );
}
