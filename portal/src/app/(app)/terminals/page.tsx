"use client";

import { useState } from "react";
import { useTerminalList, useCreateTerminal, useUpdateTerminal, useDeleteTerminal, usePingTerminal } from "@/hooks/useTerminals";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Button from "@/components/ui/button/Button";
import Input from "@/components/form/input/InputField";
import Label from "@/components/form/Label";
import StatusBadge from "@/components/common/StatusBadge";
import Pagination from "@/components/tables/Pagination";
import EmptyState from "@/components/common/EmptyState";
import ConfirmDialog from "@/components/common/ConfirmDialog";
import ActionMenu from "@/components/common/ActionMenu";
import { Modal } from "@/components/ui/modal";
import { useModal } from "@/hooks/useModal";
import { formatRelativeTime } from "@/lib/format";
import { Terminal } from "@/types/terminal";
import { PencilIcon, TrashBinIcon, BoltIcon } from "@/icons";

export default function TerminalsPage() {
  const createModal = useModal();
  const editModal = useModal();
  const [page, setPage] = useState(1);
  const perPage = 20;

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [revealedKey, setRevealedKey] = useState<string | null>(null);
  const [editingTerminal, setEditingTerminal] = useState<Terminal | null>(null);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editLoc, setEditLoc] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const { data, isLoading } = useTerminalList({ page, per_page: perPage });
  const createMutation = useCreateTerminal();
  const updateMutation = useUpdateTerminal();
  const deleteMutation = useDeleteTerminal();
  const pingMutation = usePingTerminal();

  const handleCreate = () => {
    if (!name.trim()) return;
    createMutation.mutate(
      { name, description: description || undefined, location: location || undefined },
      {
        onSuccess: (res) => {
          setName("");
          setDescription("");
          setLocation("");
          if (res.api_key) {
            setRevealedKey(res.api_key);
          }
          createModal.closeModal();
        },
      }
    );
  };

  const openEdit = (terminal: Terminal) => {
    setEditingTerminal(terminal);
    setEditName(terminal.name);
    setEditDesc(terminal.description || "");
    setEditLoc(terminal.location || "");
    editModal.openModal();
  };

  const handleUpdate = () => {
    if (!editingTerminal) return;
    updateMutation.mutate(
      { id: editingTerminal.id, data: { name: editName, description: editDesc || undefined, location: editLoc || undefined } },
      { onSuccess: () => editModal.closeModal() }
    );
  };

  const handleDelete = () => {
    if (!deleteTarget) return;
    deleteMutation.mutate(deleteTarget, { onSuccess: () => setDeleteTarget(null) });
  };

  return (
    <div>
      <PageBreadcrumb pageTitle="Terminals" />

      <div className="mb-6 flex items-center gap-3">
        <Button onClick={() => { setRevealedKey(null); createModal.openModal(); }}>Add Terminal</Button>
        {revealedKey && (
          <div className="flex items-center gap-2 rounded-lg bg-success-50 dark:bg-success-500/15 border border-success-200 dark:border-success-500/30 px-4 py-2">
            <span className="text-sm font-medium text-success-700 dark:text-success-400">API Key:</span>
            <code className="text-sm text-success-800 dark:text-success-300 font-mono break-all">{revealedKey}</code>
            <Button size="sm" variant="outline" onClick={() => { navigator.clipboard.writeText(revealedKey); }}>
              Copy
            </Button>
            <Button size="sm" variant="outline" onClick={() => setRevealedKey(null)}>Dismiss</Button>
          </div>
        )}
      </div>

      <Modal isOpen={createModal.isOpen} onClose={createModal.closeModal} className="max-w-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-6">Add Terminal</h3>
        <form onSubmit={(e) => { e.preventDefault(); handleCreate(); }} className="space-y-5">
          <div className="space-y-1.5">
            <Label>Name</Label>
            <Input placeholder="Terminal name" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="space-y-1.5">
            <Label>Description</Label>
            <Input placeholder="Optional description" value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>Location</Label>
            <Input placeholder="Store #42 - Downtown" value={location} onChange={(e) => setLocation(e.target.value)} />
          </div>
          <div className="flex gap-3 pt-2">
            <Button type="submit" disabled={createMutation.isPending}>{createMutation.isPending ? "Creating..." : "Create"}</Button>
            <Button variant="outline" onClick={createModal.closeModal}>Cancel</Button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={editModal.isOpen} onClose={editModal.closeModal} className="max-w-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-6">Edit Terminal</h3>
        <form onSubmit={(e) => { e.preventDefault(); handleUpdate(); }} className="space-y-5">
          <div className="space-y-1.5">
            <Label>Name</Label>
            <Input value={editName} onChange={(e) => setEditName(e.target.value)} required />
          </div>
          <div className="space-y-1.5">
            <Label>Description</Label>
            <Input value={editDesc} onChange={(e) => setEditDesc(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>Location</Label>
            <Input value={editLoc} onChange={(e) => setEditLoc(e.target.value)} />
          </div>
          <div className="flex gap-3 pt-2">
            <Button type="submit" disabled={updateMutation.isPending}>{updateMutation.isPending ? "Saving..." : "Save"}</Button>
            <Button variant="outline" onClick={editModal.closeModal}>Cancel</Button>
          </div>
        </form>
      </Modal>

      <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
        <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90">Terminals{data ? ` (${data.total})` : ""}</h3>
        </div>
        <div className="max-w-full overflow-x-auto">
          {isLoading ? (
            <div className="p-6 space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-12 rounded-lg bg-gray-100 dark:bg-gray-800 animate-pulse" />)}</div>
          ) : !data?.items?.length ? (
            <EmptyState
              icon={<svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>}
              title="No terminals"
              description="Add a terminal to start receiving POS interactions."
            />
          ) : (
            <table className="min-w-full">
                <thead className="border-b border-gray-100 dark:border-white/[0.05]">
                  <tr>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Name</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Location</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Status</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">API Key</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Last Seen</th>
                    <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400 sticky right-0 bg-white dark:bg-gray-900">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-white/[0.05]">
                  {data.items.map((terminal) => (
                    <tr key={terminal.id} className="hover:bg-gray-50 dark:hover:bg-white/[0.03]">
                      <td className="px-5 py-4 text-sm font-medium text-gray-800 dark:text-white/90">{terminal.name}</td>
                      <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400">{terminal.location || "—"}</td>
                      <td className="px-5 py-4 text-sm"><StatusBadge status={terminal.status} /></td>
                      <td className="px-5 py-4 text-xs font-mono text-gray-500 dark:text-gray-400">{terminal.api_key_prefix}...</td>
                      <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400">{terminal.last_seen_at ? formatRelativeTime(terminal.last_seen_at) : "Never"}</td>
                      <td className="px-5 py-4 sticky right-0 bg-white dark:bg-gray-900">
                        <ActionMenu
                          items={[
                            { label: "Edit", onClick: () => openEdit(terminal), icon: <PencilIcon className="h-4 w-4" /> },
                            ...(terminal.status === "active"
                              ? [{ label: "Ping", onClick: () => pingMutation.mutate(terminal.id), icon: <BoltIcon className="h-4 w-4" /> }]
                              : []),
                            { label: "Delete", onClick: () => setDeleteTarget(terminal.id), icon: <TrashBinIcon className="h-4 w-4" />, variant: "danger" as const },
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
        title="Delete Terminal"
        message="Are you sure you want to delete this terminal? It will be revoked and cannot be restored."
        confirmLabel="Delete"
        variant="danger"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
