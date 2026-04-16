"use client";

const TAG_STYLES: Record<string, string> = {
  items_unavailable: "bg-orange-50 text-orange-700 dark:bg-orange-500/15 dark:text-orange-400",
  swearing: "bg-red-50 text-red-700 dark:bg-red-500/15 dark:text-red-400",
  off_topic: "bg-purple-50 text-purple-700 dark:bg-purple-500/15 dark:text-purple-400",
  low_politeness: "bg-yellow-50 text-yellow-700 dark:bg-yellow-500/15 dark:text-yellow-400",
  fabrication_detected: "bg-red-50 text-red-700 dark:bg-red-500/15 dark:text-red-400",
  policy_violation: "bg-red-50 text-red-700 dark:bg-red-500/15 dark:text-red-400",
  abusive_language: "bg-red-50 text-red-700 dark:bg-red-500/15 dark:text-red-400",
  escalation_needed: "bg-blue-50 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400",
  data_privacy_concern: "bg-gray-50 text-gray-700 dark:bg-gray-500/15 dark:text-gray-400",
};

const TAG_LABELS: Record<string, string> = {
  items_unavailable: "Unavailable",
  swearing: "Swearing",
  off_topic: "Off Topic",
  low_politeness: "Low Politeness",
  fabrication_detected: "Fabrication",
  policy_violation: "Policy Violation",
  abusive_language: "Abusive",
  escalation_needed: "Escalation",
  data_privacy_concern: "Privacy",
};

interface TagBadgeProps {
  tag: string;
}

export default function TagBadge({ tag }: TagBadgeProps) {
  const style = TAG_STYLES[tag] || "bg-gray-50 text-gray-700 dark:bg-gray-500/15 dark:text-gray-400";
  const label = TAG_LABELS[tag] || tag.replace(/_/g, " ");

  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${style}`}>
      {label}
    </span>
  );
}
