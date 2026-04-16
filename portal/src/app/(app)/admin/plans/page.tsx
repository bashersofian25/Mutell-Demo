"use client";

import { useState, useEffect } from "react";
import { useAdminPlans, useAdminCreatePlan, useAdminUpdatePlan } from "@/hooks/useAdmin";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Button from "@/components/ui/button/Button";
import Input from "@/components/form/input/InputField";
import Label from "@/components/form/Label";
import StatusBadge from "@/components/common/StatusBadge";
import EmptyState from "@/components/common/EmptyState";
import ActionMenu from "@/components/common/ActionMenu";
import { Modal } from "@/components/ui/modal";
import { useModal } from "@/hooks/useModal";
import { formatNumber } from "@/lib/format";
import { Plan } from "@/types/plan";
import { PencilIcon, CheckCircleIcon, CloseLineIcon } from "@/icons";

export default function AdminPlansPage() {
  const createModal = useModal();
  const editModal = useModal();
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [maxTerminals, setMaxTerminals] = useState("5");
  const [maxUsers, setMaxUsers] = useState("10");
  const [maxSlots, setMaxSlots] = useState("1000");
  const [retention, setRetention] = useState("90");
  const [rateLimit, setRateLimit] = useState("60");

  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editMaxTerminals, setEditMaxTerminals] = useState("5");
  const [editMaxUsers, setEditMaxUsers] = useState("10");
  const [editMaxSlots, setEditMaxSlots] = useState("1000");
  const [editRetention, setEditRetention] = useState("90");
  const [editRateLimit, setEditRateLimit] = useState("60");

  const { data, isLoading } = useAdminPlans();
  const createMutation = useAdminCreatePlan();
  const updateMutation = useAdminUpdatePlan();

  const handleCreate = () => {
    if (!name.trim()) return;
    createMutation.mutate(
      {
        name,
        description: description || undefined,
        max_terminals: Number(maxTerminals),
        max_users: Number(maxUsers),
        max_slots_per_day: Number(maxSlots),
        retention_days: Number(retention),
        api_rate_limit_per_min: Number(rateLimit),
      },
      { onSuccess: () => { createModal.closeModal(); setName(""); setDescription(""); } }
    );
  };

  const openEdit = (plan: Plan) => {
    setEditingPlan(plan);
    setEditName(plan.name);
    setEditDesc(plan.description || "");
    setEditMaxTerminals(String(plan.max_terminals));
    setEditMaxUsers(String(plan.max_users));
    setEditMaxSlots(String(plan.max_slots_per_day));
    setEditRetention(String(plan.retention_days));
    setEditRateLimit(String(plan.api_rate_limit_per_min));
    editModal.openModal();
  };

  const handleUpdate = () => {
    if (!editingPlan) return;
    updateMutation.mutate(
      {
        id: editingPlan.id,
        data: {
          name: editName,
          description: editDesc || undefined,
          max_terminals: Number(editMaxTerminals),
          max_users: Number(editMaxUsers),
          max_slots_per_day: Number(editMaxSlots),
          retention_days: Number(editRetention),
          api_rate_limit_per_min: Number(editRateLimit),
        },
      },
      { onSuccess: () => editModal.closeModal() }
    );
  };

  const toggleActive = (plan: Plan) => {
    updateMutation.mutate({ id: plan.id, data: { is_active: !plan.is_active } });
  };

  return (
    <div>
      <PageBreadcrumb pageTitle="Plans" />

      <div className="mb-6">
        <Button onClick={createModal.openModal}>Create Plan</Button>
      </div>

      <Modal isOpen={createModal.isOpen} onClose={createModal.closeModal} className="max-w-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-6">Create Plan</h3>
        <div className="space-y-5">
          <div className="space-y-1.5"><Label>Name</Label><Input placeholder="Starter" value={name} onChange={(e) => setName(e.target.value)} required /></div>
          <div className="space-y-1.5"><Label>Description</Label><Input placeholder="For small businesses" value={description} onChange={(e) => setDescription(e.target.value)} /></div>
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-1.5"><Label>Max Terminals</Label><Input type="number" value={maxTerminals} onChange={(e) => setMaxTerminals(e.target.value)} /></div>
            <div className="space-y-1.5"><Label>Max Users</Label><Input type="number" value={maxUsers} onChange={(e) => setMaxUsers(e.target.value)} /></div>
            <div className="space-y-1.5"><Label>Slots / Day</Label><Input type="number" value={maxSlots} onChange={(e) => setMaxSlots(e.target.value)} /></div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5"><Label>Retention (days)</Label><Input type="number" value={retention} onChange={(e) => setRetention(e.target.value)} /></div>
            <div className="space-y-1.5"><Label>Rate Limit / min</Label><Input type="number" value={rateLimit} onChange={(e) => setRateLimit(e.target.value)} /></div>
          </div>
          <div className="flex gap-3 pt-2">
            <Button onClick={handleCreate} disabled={createMutation.isPending}>{createMutation.isPending ? "Creating..." : "Create"}</Button>
            <Button variant="outline" onClick={createModal.closeModal}>Cancel</Button>
          </div>
        </div>
      </Modal>

      <Modal isOpen={editModal.isOpen} onClose={editModal.closeModal} className="max-w-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-6">Edit Plan</h3>
        <div className="space-y-5">
          <div className="space-y-1.5"><Label>Name</Label><Input value={editName} onChange={(e) => setEditName(e.target.value)} required /></div>
          <div className="space-y-1.5"><Label>Description</Label><Input value={editDesc} onChange={(e) => setEditDesc(e.target.value)} /></div>
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-1.5"><Label>Max Terminals</Label><Input type="number" value={editMaxTerminals} onChange={(e) => setEditMaxTerminals(e.target.value)} /></div>
            <div className="space-y-1.5"><Label>Max Users</Label><Input type="number" value={editMaxUsers} onChange={(e) => setEditMaxUsers(e.target.value)} /></div>
            <div className="space-y-1.5"><Label>Slots / Day</Label><Input type="number" value={editMaxSlots} onChange={(e) => setEditMaxSlots(e.target.value)} /></div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5"><Label>Retention (days)</Label><Input type="number" value={editRetention} onChange={(e) => setEditRetention(e.target.value)} /></div>
            <div className="space-y-1.5"><Label>Rate Limit / min</Label><Input type="number" value={editRateLimit} onChange={(e) => setEditRateLimit(e.target.value)} /></div>
          </div>
          <div className="flex gap-3 pt-2">
            <Button onClick={handleUpdate} disabled={updateMutation.isPending}>{updateMutation.isPending ? "Saving..." : "Save"}</Button>
            <Button variant="outline" onClick={editModal.closeModal}>Cancel</Button>
          </div>
        </div>
      </Modal>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">{[1, 2, 3].map((i) => <div key={i} className="h-40 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse" />)}</div>
      ) : !data?.items?.length ? (
        <EmptyState title="No plans" description="Create your first plan." />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((plan) => (
            <div key={plan.id} className="rounded-2xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-white/[0.03]">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90">{plan.name}</h3>
                <StatusBadge status={plan.is_active ? "active" : "revoked"} />
              </div>
              <div className="space-y-2 mb-4">
                <p className="text-sm text-gray-500 dark:text-gray-400">{plan.description || "No description"}</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <span className="text-gray-500 dark:text-gray-400">Terminals: <span className="font-medium text-gray-800 dark:text-white/90">{plan.max_terminals}</span></span>
                  <span className="text-gray-500 dark:text-gray-400">Users: <span className="font-medium text-gray-800 dark:text-white/90">{plan.max_users}</span></span>
                  <span className="text-gray-500 dark:text-gray-400">Slots/day: <span className="font-medium text-gray-800 dark:text-white/90">{formatNumber(plan.max_slots_per_day)}</span></span>
                  <span className="text-gray-500 dark:text-gray-400">Retention: <span className="font-medium text-gray-800 dark:text-white/90">{plan.retention_days}d</span></span>
                </div>
                {plan.allowed_ai_providers.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {plan.allowed_ai_providers.map((p) => (
                      <span key={p} className="px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-xs text-gray-600 dark:text-gray-400">{p}</span>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex items-center justify-between">
                <ActionMenu
                  items={[
                    { label: "Edit", onClick: () => openEdit(plan), icon: <PencilIcon className="h-4 w-4" /> },
                    { label: plan.is_active ? "Deactivate" : "Activate", onClick: () => toggleActive(plan), icon: plan.is_active ? <CloseLineIcon className="h-4 w-4" /> : <CheckCircleIcon className="h-4 w-4" /> },
                  ]}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
