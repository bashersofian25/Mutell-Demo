import React from "react";

interface ScoreBarProps {
  label: string;
  score: number | null;
  showValue?: boolean;
}

export default function ScoreBar({ label, score, showValue = true }: ScoreBarProps) {
  const value = score ?? 0;
  const color =
    value >= 80 ? "bg-success-500" : value >= 60 ? "bg-brand-500" : value >= 40 ? "bg-warning-500" : "bg-error-500";
  const textColor =
    value >= 80
      ? "text-success-600 dark:text-success-500"
      : value >= 60
        ? "text-brand-600 dark:text-brand-400"
        : value >= 40
          ? "text-warning-600 dark:text-warning-500"
          : "text-error-600 dark:text-error-500";

  return (
    <div className="flex items-center gap-4">
      <span className="w-32 text-sm text-gray-600 dark:text-gray-400 shrink-0">{label}</span>
      <div className="flex-1 h-2.5 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${value}%` }}
        />
      </div>
      {showValue && (
        <span className={`text-sm font-semibold w-12 text-right ${textColor}`}>
          {score !== null ? `${Math.round(value)}%` : "—"}
        </span>
      )}
    </div>
  );
}
