"use client";

import React from "react";
import { Modal } from "@/components/ui/modal/index";
import Button from "@/components/ui/button/Button";

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title?: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "warning" | "primary";
  isLoading?: boolean;
}

export default function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title = "Confirm Action",
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "danger",
  isLoading = false,
}: ConfirmDialogProps) {
  const variantStyles: Record<string, string> = {
    danger: "bg-error-500 hover:bg-error-600",
    warning: "bg-warning-500 hover:bg-warning-600",
    primary: "bg-brand-500 hover:bg-brand-600",
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} className="max-w-[420px] p-6">
      <div className="space-y-4">
        <div className="flex items-start gap-4">
          <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${variant === "danger" ? "bg-error-100 dark:bg-error-500/15" : variant === "warning" ? "bg-warning-100 dark:bg-warning-500/15" : "bg-brand-100 dark:bg-brand-500/15"}`}>
            {variant === "danger" ? (
              <svg className="h-5 w-5 text-error-500 dark:text-error-400" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" /></svg>
            ) : variant === "warning" ? (
              <svg className="h-5 w-5 text-warning-500 dark:text-warning-400" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" /></svg>
            ) : (
              <svg className="h-5 w-5 text-brand-500 dark:text-brand-400" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" /></svg>
            )}
          </div>
          <div>
            <h4 className="text-lg font-semibold text-gray-800 dark:text-white/90">{title}</h4>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{message}</p>
          </div>
        </div>
        <div className="flex items-center justify-end gap-3 pt-2">
          <Button size="sm" variant="outline" onClick={onClose} disabled={isLoading}>
            {cancelLabel}
          </Button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium text-white shadow-theme-xs transition-colors disabled:opacity-50 ${variantStyles[variant]}`}
          >
            {isLoading ? (
              <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
            ) : null}
            {confirmLabel}
          </button>
        </div>
      </div>
    </Modal>
  );
}
