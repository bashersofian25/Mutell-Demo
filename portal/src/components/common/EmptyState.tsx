import React from "react";

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export default function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      {icon && <div className="mb-4 text-gray-300 dark:text-gray-600">{icon}</div>}
      <h3 className="text-lg font-semibold text-gray-800 dark:text-white/90">{title}</h3>
      {description && <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 max-w-sm">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
