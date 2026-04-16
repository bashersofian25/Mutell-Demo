"use client";

import { useRef, useEffect, useCallback } from "react";

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  opacity: number;
  opacityTarget: number;
  opacitySpeed: number;
}

const NODE_COUNT = 30;
const CONNECTION_DISTANCE = 150;
const NODE_SPEED = 0.3;

function createNode(width: number, height: number): Node {
  return {
    x: Math.random() * width,
    y: Math.random() * height,
    vx: (Math.random() - 0.5) * NODE_SPEED * 2,
    vy: (Math.random() - 0.5) * NODE_SPEED * 2,
    radius: 3 + Math.random() * 4,
    opacity: 0.3 + Math.random() * 0.5,
    opacityTarget: 0.1 + Math.random() * 0.6,
    opacitySpeed: 0.002 + Math.random() * 0.005,
  };
}

export default function NetworkAnimation() {
  const containerRef = useRef<HTMLDivElement>(null);
  const nodesRef = useRef<Node[]>([]);
  const svgRef = useRef<SVGSVGElement>(null);
  const nodeElsRef = useRef<(HTMLDivElement | null)[]>([]);
  const rafRef = useRef<number>(0);
  const sizeRef = useRef({ width: 0, height: 0 });

  const ensureNodes = useCallback(() => {
    const { width, height } = sizeRef.current;
    if (width === 0 || height === 0) return;
    if (nodesRef.current.length === 0) {
      nodesRef.current = Array.from({ length: NODE_COUNT }, () =>
        createNode(width, height)
      );
    }
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const updateSize = () => {
      const rect = container.getBoundingClientRect();
      sizeRef.current = { width: rect.width, height: rect.height };
      ensureNodes();
    };

    updateSize();
    const observer = new ResizeObserver(updateSize);
    observer.observe(container);
    return () => observer.disconnect();
  }, [ensureNodes]);

  useEffect(() => {
    const animate = () => {
      const { width, height } = sizeRef.current;
      const nodes = nodesRef.current;
      const nodeEls = nodeElsRef.current;
      const svg = svgRef.current;

      if (width === 0 || height === 0 || nodes.length === 0) {
        rafRef.current = requestAnimationFrame(animate);
        return;
      }

      let lines = "";

      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i];

        node.x += node.vx;
        node.y += node.vy;

        if (node.x < 0 || node.x > width) {
          node.vx *= -1;
          node.x = Math.max(0, Math.min(width, node.x));
        }
        if (node.y < 0 || node.y > height) {
          node.vy *= -1;
          node.y = Math.max(0, Math.min(height, node.y));
        }

        if (Math.abs(node.opacity - node.opacityTarget) < node.opacitySpeed) {
          node.opacityTarget = 0.1 + Math.random() * 0.6;
          node.opacitySpeed = 0.002 + Math.random() * 0.005;
        }
        if (node.opacity < node.opacityTarget) {
          node.opacity = Math.min(node.opacity + node.opacitySpeed, node.opacityTarget);
        } else {
          node.opacity = Math.max(node.opacity - node.opacitySpeed, node.opacityTarget);
        }

        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < CONNECTION_DISTANCE) {
            const alpha = ((1 - dist / CONNECTION_DISTANCE) * 0.25).toFixed(3);
            lines += `<line x1="${nodes[i].x.toFixed(1)}" y1="${nodes[i].y.toFixed(1)}" x2="${nodes[j].x.toFixed(1)}" y2="${nodes[j].y.toFixed(1)}" stroke="rgba(70,103,255,${alpha})" stroke-width="1"/>`;
          }
        }

        const el = nodeEls[i];
        if (el) {
          el.style.transform = `translate(${(node.x - node.radius).toFixed(1)}px, ${(node.y - node.radius).toFixed(1)}px)`;
          el.style.opacity = node.opacity.toFixed(3);
          const d = (node.radius * 2).toFixed(1);
          el.style.width = `${d}px`;
          el.style.height = `${d}px`;
        }
      }

      if (svg) {
        svg.innerHTML = lines;
      }

      rafRef.current = requestAnimationFrame(animate);
    };

    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full overflow-hidden bg-brand-950"
    >
      <svg
        ref={svgRef}
        className="absolute inset-0 w-full h-full pointer-events-none"
        style={{ zIndex: 1 }}
      />

      <div
        className="absolute inset-0 pointer-events-none"
        style={{ zIndex: 2 }}
      >
        {Array.from({ length: NODE_COUNT }).map((_, i) => (
          <div
            key={i}
            ref={(el) => { nodeElsRef.current[i] = el; }}
            className="absolute top-0 left-0 rounded-full"
            style={{
              background: "radial-gradient(circle, rgba(99,132,255,0.8) 0%, rgba(70,103,255,0.4) 100%)",
              boxShadow: "0 0 6px 1px rgba(70,103,255,0.3)",
              willChange: "transform, opacity",
              opacity: 0,
            }}
          />
        ))}
      </div>

      <div className="absolute inset-0 z-10 flex flex-col items-center justify-center pointer-events-none">
        <div className="flex flex-col items-center max-w-xs">
          <img
            src="/mutell-logo.svg"
            alt="Mutell"
            className="h-44 w-auto mb-4 invert"
          />
          <h2 className="text-2xl font-bold text-white mb-4">Mutell</h2>
          <p className="text-center text-gray-400">
            AI-Powered Point of Sale Interaction Monitoring and Evaluation
            Platform
          </p>
        </div>
      </div>
    </div>
  );
}
