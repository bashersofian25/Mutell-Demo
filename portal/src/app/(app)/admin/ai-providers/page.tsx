"use client";

import { useState } from "react";
import { useAdminAIProviders, useAdminUpdateAIProvider, useAdminAddProviderModel, useAdminRemoveProviderModel } from "@/hooks/useAdmin";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Button from "@/components/ui/button/Button";
import Input from "@/components/form/input/InputField";
import Label from "@/components/form/Label";
import StatusBadge from "@/components/common/StatusBadge";
import ActionMenu from "@/components/common/ActionMenu";
import { Modal } from "@/components/ui/modal";
import { useModal } from "@/hooks/useModal";
import { AIProvider } from "@/types/ai";
import toast from "react-hot-toast";
import { PencilIcon, TrashBinIcon, BoltIcon } from "@/icons";

export default function AIProvidersPage() {
  const editModal = useModal();
  const modelModal = useModal();
  const [editingProvider, setEditingProvider] = useState<AIProvider | null>(null);
  const [editName, setEditName] = useState("");
  const [newModel, setNewModel] = useState("");
  const [modelProvider, setModelProvider] = useState<AIProvider | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState("");

  const { data: providers, isLoading } = useAdminAIProviders();
  const updateMutation = useAdminUpdateAIProvider();
  const addModelMutation = useAdminAddProviderModel();
  const removeModelMutation = useAdminRemoveProviderModel();

  const openEdit = (provider: AIProvider) => {
    setEditingProvider(provider);
    setEditName(provider.display_name);
    editModal.openModal();
  };

  const handleUpdate = () => {
    if (!editingProvider) return;
    updateMutation.mutate(
      { id: editingProvider.id, data: { display_name: editName } },
      { onSuccess: () => editModal.closeModal() }
    );
  };

  const toggleActive = (provider: AIProvider) => {
    updateMutation.mutate({ id: provider.id, data: { is_active: !provider.is_active } });
  };

  const openModelManager = (provider: AIProvider) => {
    setModelProvider(provider);
    setNewModel("");
    modelModal.openModal();
  };

  const handleAddModel = () => {
    if (!newModel.trim() || !modelProvider) return;
    addModelMutation.mutate(
      { providerId: modelProvider.id, modelId: newModel.trim() },
      {
        onSuccess: (updated) => {
          setNewModel("");
          if (updated) setModelProvider(updated);
        },
      }
    );
  };

  const handleRemoveModel = (modelId: string) => {
    if (!modelProvider) return;
    removeModelMutation.mutate(
      { providerId: modelProvider.id, modelId },
      {
        onSuccess: (updated) => {
          if (updated) setModelProvider(updated);
        },
      }
    );
  };

  const handleSaveApiKey = () => {
    if (!apiKeyInput.trim() || !editingProvider) return;
    updateMutation.mutate(
      { id: editingProvider.id, data: { api_key: apiKeyInput.trim() } },
      {
        onSuccess: () => {
          setApiKeyInput("");
          toast.success("API key saved");
        },
      }
    );
  };

  return (
    <div>
      <PageBreadcrumb pageTitle="AI Providers" />

      <Modal isOpen={editModal.isOpen} onClose={editModal.closeModal} className="max-w-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-6">Edit AI Provider</h3>
        <div className="space-y-5">
          <div className="space-y-1.5">
            <Label>Slug</Label>
            <Input value={editingProvider?.slug || ""} disabled />
          </div>
          <div className="space-y-1.5">
            <Label>Display Name</Label>
            <Input value={editName} onChange={(e) => setEditName(e.target.value)} required />
          </div>
          <div className="space-y-1.5">
            <Label>Provider API Key</Label>
            <div className="flex gap-2">
              <Input
                type="password"
                placeholder="Enter provider API key"
                value={apiKeyInput}
                onChange={(e) => setApiKeyInput(e.target.value)}
              />
              <Button size="sm" onClick={handleSaveApiKey} disabled={!apiKeyInput.trim()}>Save</Button>
            </div>
            <p className="text-xs text-gray-400">Used by all tenants who configure this provider</p>
          </div>
          <div className="flex gap-3 pt-2">
            <Button onClick={handleUpdate} disabled={updateMutation.isPending}>{updateMutation.isPending ? "Saving..." : "Save"}</Button>
            <Button variant="outline" onClick={editModal.closeModal}>Cancel</Button>
          </div>
        </div>
      </Modal>

      <Modal isOpen={modelModal.isOpen} onClose={modelModal.closeModal} className="max-w-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90 mb-4">
          Models — {modelProvider?.display_name}
        </h3>
        {modelProvider?.supported_models && modelProvider.supported_models.length > 0 ? (
          <div className="space-y-2 mb-4">
            {modelProvider.supported_models.map((model) => (
              <div key={model} className="flex items-center justify-between rounded-lg border border-gray-200 dark:border-gray-700 px-3 py-2">
                <span className="text-sm font-mono text-gray-800 dark:text-gray-200">{model}</span>
                <button
                  onClick={() => handleRemoveModel(model)}
                  className="text-xs text-error-500 hover:text-error-600 font-medium"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">No models configured for this provider.</p>
        )}
        <div className="flex gap-2">
          <Input
            placeholder="e.g., gpt-4-turbo"
            value={newModel}
            onChange={(e) => setNewModel(e.target.value)}
          />
          <Button size="sm" onClick={handleAddModel} disabled={!newModel.trim()}>Add</Button>
        </div>
        <div className="flex justify-end mt-4">
          <Button variant="outline" onClick={modelModal.closeModal}>Close</Button>
        </div>
      </Modal>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {isLoading ? (
          [1, 2, 3].map((i) => <div key={i} className="h-52 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse" />)
        ) : !providers?.length ? (
          <div className="col-span-full text-center py-12 text-gray-500 dark:text-gray-400">No AI providers configured</div>
        ) : (
          providers.map((provider) => (
            <div key={provider.id} className="rounded-2xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-white/[0.03] transition-colors duration-200 hover:border-brand-300 dark:hover:border-brand-700">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90">{provider.display_name}</h3>
                <StatusBadge status={provider.is_active ? "active" : "revoked"} />
              </div>
              <p className="text-xs font-mono text-gray-500 dark:text-gray-400 mb-3">{provider.slug}</p>
              {provider.supported_models && provider.supported_models.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {provider.supported_models.map((model) => (
                    <span key={model} className="px-2 py-0.5 rounded-full bg-brand-50 dark:bg-brand-500/10 text-xs text-brand-600 dark:text-brand-400 font-medium">{model}</span>
                  ))}
                </div>
              )}
              <div className="flex items-center justify-between pt-2 border-t border-gray-100 dark:border-gray-800">
                <StatusBadge status={provider.is_active ? "active" : "revoked"} />
                <ActionMenu
                  items={[
                    { label: "Edit", onClick: () => openEdit(provider), icon: <PencilIcon className="h-4 w-4" /> },
                    { label: "Models", onClick: () => openModelManager(provider), icon: <BoltIcon className="h-4 w-4" /> },
                    { label: provider.is_active ? "Disable" : "Enable", onClick: () => toggleActive(provider), icon: <TrashBinIcon className="h-4 w-4" /> },
                  ]}
                />
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
