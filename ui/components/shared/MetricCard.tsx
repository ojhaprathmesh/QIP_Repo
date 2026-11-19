'use client';

import React from 'react';
import { motion } from 'framer-motion';

export interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  delta?: number;
  color?: 'cyan' | 'violet' | 'emerald' | 'coral';
}

const colorStyles: Record<
  NonNullable<MetricCardProps['color']>,
  { border: string; glow: string; text: string; accent: string }
> = {
  cyan: {
    border: 'border-[#00f5ff]/25',
    glow: 'hover:shadow-[0_0_15px_rgba(0,245,255,0.15)]',
    text: 'text-[#00f5ff]',
    accent: 'bg-[#00f5ff]',
  },
  violet: {
    border: 'border-[#a855f7]/25',
    glow: 'hover:shadow-[0_0_15px_rgba(168,85,247,0.15)]',
    text: 'text-[#a855f7]',
    accent: 'bg-[#a855f7]',
  },
  emerald: {
    border: 'border-[#10b981]/25',
    glow: 'hover:shadow-[0_0_15px_rgba(16,185,129,0.15)]',
    text: 'text-[#10b981]',
    accent: 'bg-[#10b981]',
  },
  coral: {
    border: 'border-[#f43f5e]/25',
    glow: 'hover:shadow-[0_0_15px_rgba(244,63,94,0.15)]',
    text: 'text-[#f43f5e]',
    accent: 'bg-[#f43f5e]',
  },
};

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  unit,
  delta,
  color = 'cyan',
}) => {
  const styles = colorStyles[color] || colorStyles.cyan;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className={`relative overflow-hidden rounded-xl bg-white/[0.03] backdrop-blur-md border ${styles.border} ${styles.glow} p-5 transition-all duration-300`}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-xs uppercase font-medium tracking-wider text-slate-400">
          {label}
        </span>
        {delta !== undefined && (
          <span
            className={`inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-md border ${
              delta >= 0
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
            }`}
          >
            {delta >= 0 ? `+${delta}` : delta}
            {unit ? `%` : ''}
          </span>
        )}
      </div>

      <div className="flex items-baseline gap-1.5">
        <span className="text-2xl font-bold tracking-tight text-white mono">
          {value}
        </span>
        {unit && <span className="text-xs font-medium text-slate-400">{unit}</span>}
      </div>

      <div
        className={`absolute bottom-0 left-0 right-0 h-[2px] opacity-40 ${styles.accent}`}
      />
    </motion.div>
  );
};

export default MetricCard;
