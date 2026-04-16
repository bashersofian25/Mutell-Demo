import React, { useState } from "react";

interface ChartTabProps {
  options?: { key: string; label: string }[];
  defaultOption?: string;
  onChange?: (option: string) => void;
}

const ChartTab: React.FC<ChartTabProps> = ({
  options = [
    { key: "optionOne", label: "Monthly" },
    { key: "optionTwo", label: "Quarterly" },
    { key: "optionThree", label: "Annually" },
  ],
  defaultOption = "optionOne",
  onChange,
}) => {
  const [selected, setSelected] = useState(defaultOption);

  const handleClick = (key: string) => {
    setSelected(key);
    if (onChange) onChange(key);
  };

  const getButtonClass = (key: string) =>
    selected === key
      ? "shadow-theme-xs text-gray-900 dark:text-white bg-white dark:bg-gray-800"
      : "text-gray-500 dark:text-gray-400";

  return (
    <div className="flex items-center gap-0.5 rounded-lg bg-gray-100 p-0.5 dark:bg-gray-900">
      {options.map((option) => (
        <button
          key={option.key}
          onClick={() => handleClick(option.key)}
          className={`px-3 py-2 font-medium w-full rounded-md text-theme-sm hover:text-gray-900 dark:hover:text-white ${getButtonClass(option.key)}`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
};

export default ChartTab;
