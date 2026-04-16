import React from "react";

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: { value: string; positive: boolean };
  className?: string;
}

export default function StatCard({ label, value, icon, trend, className = "" }: StatCardProps) {
  return (
    <div className={`rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03] sm:p-6 ${className}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</p>
          <p className="mt-2 text-2xl font-bold text-gray-800 dark:text-white/90">{value}</p>
        </div>
        {icon && (
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 dark:bg-brand-500/15">
            {icon}
          </div>
        )}
      </div>
      {trend && (
        <p className={`mt-2 text-xs font-medium ${trend.positive ? "text-success-600 dark:text-success-500" : "text-error-600 dark:text-error-500"}`}>
          {trend.positive ? "↑" : "↓"} {trend.value}
        </p>
      )}
    </div>
  );
}
