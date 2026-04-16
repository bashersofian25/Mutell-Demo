"use client";

import React, { useMemo } from "react";

const COLORS = [
  "rgba(70,95,255,0.25)",
  "rgba(70,95,255,0.15)",
  "rgba(99,179,237,0.2)",
  "rgba(129,140,248,0.2)",
  "rgba(167,139,250,0.18)",
  "rgba(99,179,237,0.12)",
  "rgba(70,95,255,0.1)",
  "rgba(129,140,248,0.12)",
];

const ANIMATION_DURATIONS = [4, 5, 6, 7, 8, 5.5, 6.5, 4.5, 7.5, 3.5];

function AnimatedGrid({ rows, cols, className }: { rows: number; cols: number; className?: string }) {
  const cells = useMemo(() => {
    const result: { colored: boolean; colorIndex: number; delay: number; duration: number }[] = [];
    const seed = rows * 100 + cols;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const i = r * cols + c;
        const hash = ((seed + i) * 2654435761) >>> 0;
        const colored = (hash % 10) < 3;
        result.push({
          colored,
          colorIndex: hash % COLORS.length,
          delay: (hash % 4000) / 1000,
          duration: ANIMATION_DURATIONS[hash % ANIMATION_DURATIONS.length],
        });
      }
    }
    return result;
  }, [rows, cols]);

  return (
    <div
      className={`absolute ${className || ""}`}
      style={{
        display: "grid",
        gridTemplateColumns: `repeat(${cols}, 1fr)`,
        gridTemplateRows: `repeat(${rows}, 1fr)`,
        gap: "1px",
        width: "100%",
        height: "100%",
      }}
    >
      {cells.map((cell, i) =>
        cell.colored ? (
          <div
            key={i}
            style={{
              backgroundColor: COLORS[cell.colorIndex],
              animation: `gridColorShift ${cell.duration}s ease-in-out ${cell.delay}s infinite alternate,
                         gridPulse ${cell.duration * 1.5}s ease-in-out ${cell.delay}s infinite`,
            }}
          />
        ) : (
          <div key={i} className="border border-white/[0.06]" />
        )
      )}
    </div>
  );
}

export default function GridShape() {
  return (
    <>
      <div className="absolute right-0 top-0 -z-1 w-full max-w-[250px] aspect-[16/9] xl:max-w-[450px]">
        <AnimatedGrid rows={5} cols={9} className="inset-0" />
      </div>
      <div className="absolute bottom-0 left-0 -z-1 w-full max-w-[250px] aspect-[16/9] xl:max-w-[450px] rotate-180">
        <AnimatedGrid rows={5} cols={9} className="inset-0" />
      </div>
    </>
  );
}
