'use client';

import React from 'react';
import { motion } from 'framer-motion';

export interface ImageCanvasProps {
  pixels: number[][] | null;
  size?: number; // total width/height in px, default 120
  label?: string;
  borderColor?: string;
}

export const ImageCanvas: React.FC<ImageCanvasProps> = ({
  pixels,
  size = 120,
  label,
  borderColor = 'rgba(255, 255, 255, 0.1)',
}) => {
  // If no pixels provided, render placeholder shimmer grid
  if (!pixels || pixels.length === 0 || !pixels[0] || pixels[0].length === 0) {
    const placeholderSize = 4; // 4x4 shimmer placeholder
    return (
      <div className="flex flex-col items-center gap-1.5">
        <div
          className="relative overflow-hidden rounded-lg bg-black/40 border p-1"
          style={{
            width: size,
            height: size,
            borderColor,
          }}
        >
          <div
            className="grid w-full h-full gap-0.5"
            style={{
              gridTemplateColumns: `repeat(${placeholderSize}, minmax(0, 1fr))`,
              gridTemplateRows: `repeat(${placeholderSize}, minmax(0, 1fr))`,
            }}
          >
            {Array.from({ length: placeholderSize * placeholderSize }).map((_, idx) => (
              <div
                key={idx}
                className="w-full h-full rounded-sm bg-white/5 animate-pulse"
                style={{
                  animationDelay: `${(idx % placeholderSize) * 100}ms`,
                }}
              />
            ))}
          </div>
        </div>
        {label && <span className="text-xs text-slate-400 font-mono text-center">{label}</span>}
      </div>
    );
  }

  const height = pixels.length;
  const width = pixels[0].length;

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div
        className="relative overflow-hidden rounded-lg bg-black/60 border p-1"
        style={{
          width: size,
          height: size,
          borderColor,
        }}
      >
        <div
          className="grid w-full h-full gap-[1px]"
          style={{
            gridTemplateColumns: `repeat(${width}, minmax(0, 1fr))`,
            gridTemplateRows: `repeat(${height}, minmax(0, 1fr))`,
          }}
        >
          {pixels.map((row, rIdx) =>
            row.map((val, cIdx) => {
              const clamped = Math.max(0, Math.min(1, val));
              // Map 0 -> dark (#0a0a0a), 1 -> white (#ffffff)
              // In RGB: 0a -> 10, ff -> 255
              const intensity = Math.round(10 + clamped * (255 - 10));
              const hex = intensity.toString(16).padStart(2, '0');
              const bgColor = `#${hex}${hex}${hex}`;
              const cellIndex = rIdx * width + cIdx;

              return (
                <motion.div
                  key={`${rIdx}-${cIdx}`}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{
                    duration: 0.2,
                    delay: cellIndex * 0.002, // index * 2ms stagger delay
                  }}
                  className="w-full h-full rounded-[1px]"
                  style={{ backgroundColor: bgColor }}
                  title={`[${rIdx}, ${cIdx}]: ${clamped.toFixed(3)}`}
                />
              );
            })
          )}
        </div>
      </div>
      {label && <span className="text-xs text-slate-400 font-mono text-center">{label}</span>}
    </div>
  );
};

export default ImageCanvas;
