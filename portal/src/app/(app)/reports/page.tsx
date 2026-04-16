"use client";

import { useState } from "react";
import { format } from "date-fns";
import { useReportList, useCreateReport, useDownloadReport, useDeleteReport } from "@/hooks/useReports";
import { useTerminalList } from "@/hooks/useTerminals";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Button from "@/components/ui/button/Button";
import StatusBadge from "@/components/common/StatusBadge";
import Pagination from "@/components/tables/Pagination";
import EmptyState from "@/components/common/EmptyState";
import ConfirmDialog from "@/components/common/ConfirmDialog";
import ActionMenu from "@/components/common/ActionMenu";
import { Modal } from "@/components/ui/modal";
import Input from "@/components/form/input/InputField";
import Label from "@/components/form/Label";
import DatePicker from "@/components/form/date-picker";
import { useModal } from "@/hooks/useModal";
import { formatRelativeTime, truncate } from "@/lib/format";
import { useCanManageReports } from "@/lib/hooks";
import { DownloadIcon, TrashBinIcon } from "@/icons";

export default function ReportsPage() {
  const [page, setPage] = useState(1);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const canManage = useCanManageReports();
  const perPage = 20;

  const { data, isLoading } = useReportList({ page, per_page: perPage });
  const createReport = useCreateReport();
  const downloadReport = useDownloadReport();
  const deleteReport = useDeleteReport();

  const { isOpen, openModal, closeModal } = useModal();
  const [title, setTitle] = useState("");
  const [periodStart, setPeriodStart] = useState("");
  const [periodEnd, setPeriodEnd] = useState("");
  const [includeTranscripts, setIncludeTranscripts] = useState(false);
  const [includeNotes, setIncludeNotes] = useState(true);

  const handleCreate = () => {
    if (!title.trim() || !periodStart || !periodEnd) return;
    createReport.mutate(
      {
        title,
        period_start: new Date(periodStart).toISOString(),
        period_end: new Date(periodEnd).toISOString(),
        include_transcripts: includeTranscripts,
        include_notes: includeNotes,
      },
      { onSuccess: () => { closeModal(); setTitle(""); setPeriodStart(""); setPeriodEnd(""); } }
    );
  };

  const handleDelete = () => {
    if (!deleteTarget) return;
    deleteReport.mutate(deleteTarget, { onSuccess: () => setDeleteTarget(null) });
  };

  return (
    <div>
      <PageBreadcrumb pageTitle="Reports" />

      {canManage && (
        <div className="mb-6">
          <Button onClick={openModal}>Generate Report</Button>
        </div>
      )}

      <Modal isOpen={isOpen} onClose={closeModal} className="max-w-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-6">Generate Report</h3>
        <div className="space-y-5">
          <div className="space-y-1.5">
            <Label>Title</Label>
            <Input placeholder="Weekly Quality Report" value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <DatePicker
                id="report-period-start"
                label="Period Start"
                placeholder="Select start date"
                onChange={([date]: Date[]) => { if (date) setPeriodStart(date.toISOString().split("T")[0]); }}
              />
            </div>
            <div className="space-y-1.5">
              <DatePicker
                id="report-period-end"
                label="Period End"
                placeholder="Select end date"
                onChange={([date]: Date[]) => { if (date) setPeriodEnd(date.toISOString().split("T")[0]); }}
              />
            </div>
          </div>
          <div className="flex items-center gap-6">
            <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
              <input type="checkbox" checked={includeTranscripts} onChange={(e) => setIncludeTranscripts(e.target.checked)} className="h-4 w-4 rounded border-gray-300" />
              Include transcripts
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
              <input type="checkbox" checked={includeNotes} onChange={(e) => setIncludeNotes(e.target.checked)} className="h-4 w-4 rounded border-gray-300" />
              Include notes
            </label>
          </div>
          <div className="flex gap-3 pt-2">
            <Button onClick={handleCreate} disabled={!title.trim() || !periodStart || !periodEnd || createReport.isPending}>
              {createReport.isPending ? "Generating..." : "Generate"}
            </Button>
            <Button variant="outline" onClick={closeModal}>Cancel</Button>
          </div>
        </div>
      </Modal>

      <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
        <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90">{`Reports${data ? ` (${data.total})` : ""}`}</h3>
        </div>
        <div className="max-w-full overflow-x-auto">
          {isLoading ? (
            <div className="p-6 space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-12 rounded-lg bg-gray-100 dark:bg-gray-800 animate-pulse" />)}</div>
          ) : !data?.items?.length ? (
            <EmptyState
              icon={<svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>}
              title="No reports yet"
              description="Generate your first report to get started."
            />
          ) : (
              <table className="min-w-full">
                <thead className="border-b border-gray-100 dark:border-white/[0.05]">
                  <tr>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Title</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Status</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Period</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Created</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-white/[0.05]">
                  {data.items.map((report) => (
                    <tr key={report.id} className="hover:bg-gray-50 dark:hover:bg-white/[0.03]">
                      <td className="px-5 py-4 text-sm font-medium text-gray-800 dark:text-white/90">{report.title}</td>
                      <td className="px-5 py-4 text-sm"><StatusBadge status={report.status} /></td>
                      <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400">
                        {format(new Date(report.period_start), "MMM dd")} — {format(new Date(report.period_end), "MMM dd, yyyy")}
                      </td>
                      <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400">{formatRelativeTime(report.created_at)}</td>
                      <td className="px-5 py-4">
                        <ActionMenu
                          items={[
                            ...(report.status === "ready"
                              ? [{ label: "Download", onClick: () => downloadReport.mutate(report.id), icon: <DownloadIcon className="h-4 w-4" /> }]
                              : []),
                            ...(canManage
                              ? [{ label: "Delete", onClick: () => setDeleteTarget(report.id), icon: <TrashBinIcon className="h-4 w-4" />, variant: "danger" as const }]
                              : []),
                          ]}
                        />
                      </td>
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
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete Report"
        message="Are you sure you want to delete this report? This action cannot be undone."
        confirmLabel="Delete"
        variant="danger"
        isLoading={deleteReport.isPending}
      />
    </div>
  );
}
