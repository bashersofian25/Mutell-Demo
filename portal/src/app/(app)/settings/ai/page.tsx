"use client";

import { useState } from "react";
import { useAIConfigs, useAIProviders, useCreateAIConfig, useUpdateAIConfig, useDeleteAIConfig } from "@/hooks/useAISettings";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Button from "@/components/ui/button/Button";
import Input from "@/components/form/input/InputField";
import Label from "@/components/form/Label";
import Select from "@/components/form/Select";
import TextArea from "@/components/form/input/TextArea";
import { Modal } from "@/components/ui/modal";
import ConfirmDialog from "@/components/common/ConfirmDialog";
import StatusBadge from "@/components/common/StatusBadge";
import EmptyState from "@/components/common/EmptyState";
import ActionMenu from "@/components/common/ActionMenu";
import { useModal } from "@/hooks/useModal";
import { useIsTenantAdmin } from "@/lib/hooks";
import { AIConfig, AIProviderOption } from "@/types/ai";
import { PencilIcon, TrashBinIcon } from "@/icons";

export default function AISettingsPage() {
  const isAdmin = useIsTenantAdmin();
  const addModal = useModal();
  const editModal = useModal();
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const { data: configsData, isLoading } = useAIConfigs();
  const { data: providers } = useAIProviders();
  const createConfig = useCreateAIConfig();
  const updateConfig = useUpdateAIConfig();
  const deleteConfig = useDeleteAIConfig();

  const configs = configsData?.items || [];

  const [providerId, setProviderId] = useState("");
  const [modelId, setModelId] = useState("");
  const [isDefault, setIsDefault] = useState(false);
  const [customPrompt, setCustomPrompt] = useState("");

  const [editingConfig, setEditingConfig] = useState<AIConfig | null>(null);
  const [editModelId, setEditModelId] = useState("");
  const [editIsDefault, setEditIsDefault] = useState(false);
  const [editCustomPrompt, setEditCustomPrompt] = useState("");

  const providerOptions = (providers || []).map((p: AIProviderOption) => ({ value: p.id, label: p.display_name }));
  const modelsForProvider = (providers || []).find((p: AIProviderOption) => p.id === providerId)?.supported_models || [];
  const modelOptions = modelsForProvider.length > 0
    ? modelsForProvider.map((m: string) => ({ value: m, label: m }))
    : [{ value: "", label: "No models available" }];

  const editProviderModels = (providers || []).find((p: AIProviderOption) => p.id === editingConfig?.provider_id)?.supported_models || [];
  const editModelOptions = editProviderModels.length > 0
    ? editProviderModels.map((m: string) => ({ value: m, label: m }))
    : [{ value: "", label: "No models available" }];

  const handleCreate = () => {
    if (!providerId || !modelId) return;
    createConfig.mutate(
      { provider_id: providerId, model_id: modelId, is_default: isDefault, custom_prompt: customPrompt || undefined },
      { onSuccess: () => { addModal.closeModal(); setProviderId(""); setModelId(""); setIsDefault(false); setCustomPrompt(""); } }
    );
  };

  const openEdit = (config: AIConfig) => {
    setEditingConfig(config);
    setEditModelId(config.model_id);
    setEditIsDefault(config.is_default);
    setEditCustomPrompt(config.custom_prompt || "");
    editModal.openModal();
  };

  const handleUpdate = () => {
    if (!editingConfig) return;
    updateConfig.mutate(
      {
        id: editingConfig.id,
        data: {
          model_id: editModelId,
          is_default: editIsDefault,
          custom_prompt: editCustomPrompt || undefined,
        },
      },
      { onSuccess: () => editModal.closeModal() }
    );
  };

  const handleDelete = () => {
    if (!deleteTarget) return;
    deleteConfig.mutate(deleteTarget, { onSuccess: () => setDeleteTarget(null) });
  };

  return (
    <div>
      <PageBreadcrumb pageTitle="AI Configuration" />

      {isAdmin && (
        <div className="mb-6">
          <Button onClick={addModal.openModal}>Add AI Configuration</Button>
        </div>
      )}

      <Modal isOpen={addModal.isOpen} onClose={addModal.closeModal} className="max-w-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-6">Add AI Configuration</h3>
        <div className="space-y-5">
          <div className="space-y-1.5">
            <Label>Provider</Label>
            <Select options={providerOptions.length > 0 ? providerOptions : [{ value: "", label: "No providers available" }]} defaultValue={providerId} onChange={setProviderId} />
          </div>
          <div className="space-y-1.5">
            <Label>Model</Label>
            <Select options={modelOptions} defaultValue={modelId} onChange={setModelId} />
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
            <input type="checkbox" checked={isDefault} onChange={(e) => setIsDefault(e.target.checked)} className="h-4 w-4 rounded border-gray-300" />
            Set as default
          </label>
          <div className="space-y-1.5">
            <Label>Custom Prompt</Label>
            <TextArea value={customPrompt} onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setCustomPrompt(e.target.value)} rows={3} placeholder="Optional custom evaluation instructions..." />
          </div>
          <div className="flex gap-3 pt-2">
            <Button onClick={handleCreate} disabled={createConfig.isPending}>{createConfig.isPending ? "Adding..." : "Add Configuration"}</Button>
            <Button variant="outline" onClick={addModal.closeModal}>Cancel</Button>
          </div>
        </div>
      </Modal>

      <Modal isOpen={editModal.isOpen} onClose={editModal.closeModal} className="max-w-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-6">Edit AI Configuration</h3>
        <div className="space-y-5">
          <div className="space-y-1.5">
            <Label>Provider</Label>
            <Input value={editingConfig?.provider_name || ""} disabled />
          </div>
          <div className="space-y-1.5">
            <Label>Model</Label>
            <Select options={editModelOptions} defaultValue={editModelId} onChange={setEditModelId} />
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
            <input type="checkbox" checked={editIsDefault} onChange={(e) => setEditIsDefault(e.target.checked)} className="h-4 w-4 rounded border-gray-300" />
            Set as default
          </label>
          <div className="space-y-1.5">
            <Label>Custom Prompt</Label>
            <TextArea value={editCustomPrompt} onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setEditCustomPrompt(e.target.value)} rows={3} />
          </div>
          <div className="flex gap-3 pt-2">
            <Button onClick={handleUpdate} disabled={updateConfig.isPending}>{updateConfig.isPending ? "Saving..." : "Save"}</Button>
            <Button variant="outline" onClick={editModal.closeModal}>Cancel</Button>
          </div>
        </div>
      </Modal>

      {isLoading ? (
        <div className="space-y-4">{[1, 2].map((i) => <div key={i} className="h-32 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse" />)}</div>
      ) : configs.length === 0 ? (
        <EmptyState
          icon={<svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" /></svg>}
          title="No AI configurations"
          description="Add an AI provider configuration to start evaluating interactions."
          action={isAdmin ? <Button size="sm" onClick={addModal.openModal}>Add Configuration</Button> : undefined}
        />
      ) : (
        <div className="space-y-4">
          {configs.map((config) => (
            <div key={config.id} className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
              <div className="px-6 py-5 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 dark:bg-brand-500/15">
                    <svg className="h-5 w-5 text-brand-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3" /></svg>
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-semibold text-gray-800 dark:text-white/90">{config.provider_name}</h4>
                      {config.is_default && <span className="text-xs font-medium text-brand-500 bg-brand-50 dark:bg-brand-500/15 px-2 py-0.5 rounded-full">Default</span>}
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Model: {config.model_id}</p>
                  </div>
                </div>
                {isAdmin && (
                  <ActionMenu
                    items={[
                      { label: "Edit", onClick: () => openEdit(config), icon: <PencilIcon className="h-4 w-4" /> },
                      { label: "Delete", onClick: () => setDeleteTarget(config.id), icon: <TrashBinIcon className="h-4 w-4" />, variant: "danger" as const },
                    ]}
                  />
                )}
              </div>
              {config.custom_prompt && (
                <div className="px-6 pb-5 pt-0">
                  <div className="rounded-lg bg-gray-50 dark:bg-gray-900 p-3">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1 font-medium">Custom Prompt</p>
                    <p className="text-sm text-gray-700 dark:text-gray-300">{config.custom_prompt}</p>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete AI Configuration"
        message="Are you sure you want to delete this AI configuration?"
        confirmLabel="Delete"
        variant="danger"
        isLoading={deleteConfig.isPending}
      />
    </div>
  );
}
