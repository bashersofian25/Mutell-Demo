"use client";

import { useState } from "react";
import { Dropdown } from "@/components/ui/dropdown/Dropdown";
import { DropdownItem } from "@/components/ui/dropdown/DropdownItem";
import { MoreDotIcon } from "@/icons";

interface ActionItem {
  label: string;
  onClick: () => void;
  icon?: React.ReactNode;
  variant?: "default" | "danger";
}

interface ActionMenuProps {
  items: ActionItem[];
}

export default function ActionMenu({ items }: ActionMenuProps) {
  const [isOpen, setIsOpen] = useState(false);

  const close = () => setIsOpen(false);
  const toggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsOpen((prev) => !prev);
  };

  return (
    <div className="relative inline-block">
      <button
        onClick={toggle}
        className="dropdown-toggle rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-white/5 dark:hover:text-gray-300"
      >
        <MoreDotIcon className="h-5 w-5" />
      </button>
      <Dropdown isOpen={isOpen} onClose={close} className="w-44 p-1.5">
        {items.map((item, i) => (
          <DropdownItem
            key={i}
            onClick={item.onClick}
            onItemClick={close}
            className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium ${
              item.variant === "danger"
                ? "text-error-600 hover:bg-error-50 dark:text-error-400 dark:hover:bg-error-500/10"
                : "text-gray-700 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-white/5 dark:hover:text-white"
            }`}
          >
            {item.icon && <span className="flex-shrink-0">{item.icon}</span>}
            {item.label}
          </DropdownItem>
        ))}
      </Dropdown>
    </div>
  );
}
