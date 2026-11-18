'use client';

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useQuantumStore } from '@/lib/quantumStore';
import MetricCard from '@/components/shared/MetricCard';

export const StageTomography: React.FC = () => {
  const shotsProgress = useQuantumStore((state) => state.shotsProgress);
  const frameResult = useQuantumStore((state) => state.frameResult);
  const customPixels = useQuantumStore((state) => state.config.custom_pixels);

  const shotsCompleted = shotsProgress?.shots_completed ?? 0;
  const totalShots = shotsProgress?.total_shots || 10000;
  const pct = Math.min(100, Math.round((shotsCompleted / Math.max(1, totalShots)) * 100));

  // Bitstring histogram: sort descending and pick top 12
  const sortedBitstrings = useMemo(() => {
    if (!shotsProgress?.bitstring_counts) return [];
    return Object.entries(shotsProgress.bitstring_counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 12);
  }, [shotsProgress]);

  const maxCount = useMemo(() => {
    if (sortedBitstrings.length === 0) return 1;
    return Math.max(...sortedBitstrings.map(([, count]) => count), 1);
  }, [sortedBitstrings]);

  // Progressive raster grid: random shot noise initially that coalesces into the reconstructed image
  const rasterGrid = useMemo(() => {
    const base = frameResult?.pixels || customPixels;
    const size = base && base.length > 0 ? base.length : 8;
    const grid: number[][] = [];
    const progressFactor = shotsCompleted / Math.max(1, totalShots);

    for (let r = 0; r < size; r++) {
      const row: number[] = [];
      for (let c = 0; c < size; c++) {
        const target = base?.[r]?.[c] ?? ((r + c) % 2 === 0 ? 0.9 : 0.1);
        const noise = Math.sin(r * 12.9898 + c * 78.233 + shotsCompleted * 0.01) * 0.5 + 0.5;
        const coalesced = noise * (1 - progressFactor) + target * progressFactor;
        row.push(Math.min(1, Math.max(0, coalesced)));
      }
      grid.push(row);
    }
    return grid;
  }, [shotsCompleted, totalShots, frameResult, customPixels]);

  return (
    <div className="space-y-6">
      {/* Header & Shot Counter */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-xl border border-white/10 bg-white/5 backdrop-blur">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-[#00f5ff] animate-pulse" />
            <span className="text-xs font-mono uppercase tracking-wider text-cyan-400">
              Stage 05 // Tomography & Measurement
            </span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Shot-Based Measurement & State Tomography
          </h2>
          <p className="text-sm text-slate-400 mt-0.5">
            Quantum projective readout, projective statistics, and progressive reconstruction.
          </p>
        </div>

        {/* Shot counter badge */}
        <div className="flex flex-col items-end justify-center px-5 py-3 rounded-xl border border-cyan-500/20 bg-cyan-950/20 backdrop-blur">
          <span className="text-xs uppercase font-mono tracking-wider text-slate-400">
            Measurement Shots
          </span>
          <div className="text-xl md:text-2xl font-bold font-mono text-[#00f5ff]">
            N = {shotsCompleted.toLocaleString()} / {totalShots.toLocaleString()}
          </div>
          <span className="text-[11px] font-mono text-cyan-300/80">
            {pct}% Completed
          </span>
        </div>
      </div>

      {/* Top Section: Progress Bar */}
      <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur p-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs uppercase font-mono tracking-wider text-slate-400">
            Shot Accumulation Progress
          </span>
          <span className="text-xs font-mono font-bold text-[#00f5ff]">{pct}%</span>
        </div>
        <div className="relative w-full h-3 rounded-full bg-black/60 border border-white/5 overflow-hidden">
          <motion.div
            className="h-full bg-[#00f5ff] rounded-full shadow-[0_0_12px_#00f5ff80]"
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.35, ease: 'easeOut' }}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Middle Section: Bitstring Histogram */}
        <div className="lg:col-span-2 rounded-xl border border-white/10 bg-white/5 backdrop-blur p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs uppercase font-mono tracking-wider text-slate-400">
                Bitstring Measurement Histogram (Top 12)
              </span>
              <span className="text-xs font-mono text-cyan-400">
                {sortedBitstrings.length} states observed
              </span>
            </div>

            {sortedBitstrings.length === 0 ? (
              <div className="h-56 flex flex-col items-center justify-center border border-dashed border-white/10 rounded-lg text-slate-500 font-mono text-xs">
                <span className="animate-pulse">Awaiting measurement data...</span>
              </div>
            ) : (
              <div className="h-56 flex items-end gap-2 pt-6 pb-2 border-b border-white/10 overflow-x-auto">
                {sortedBitstrings.map(([bitstring, count]) => {
                  const barHeightPct = Math.max(8, Math.round((count / maxCount) * 100));
                  return (
                    <div
                      key={bitstring}
                      className="flex-1 flex flex-col items-center gap-2 h-full justify-end min-w-[36px]"
                    >
                      <span className="text-[10px] font-mono text-slate-400">{count}</span>
                      <motion.div
                        className="w-full bg-[#00f5ff] rounded-t-sm shadow-[0_0_8px_rgba(0,245,255,0.3)] hover:brightness-125 transition-all"
                        initial={{ height: 0 }}
                        animate={{ height: `${barHeightPct}%` }}
                        transition={{ duration: 0.4, ease: 'easeOut' }}
                        title={`|${bitstring}⟩: ${count} shots`}
                      />
                      <span className="font-mono text-xs text-slate-300 tracking-tight">
                        |{bitstring}⟩
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
          <div className="text-[11px] font-mono text-slate-500 mt-3">
            Ranked by projective frequency descending. Basis: Computational Z-basis.
          </div>
        </div>

        {/* Bottom Section: Progressive Raster Visualization */}
        <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur p-6 flex flex-col justify-between items-center text-center">
          <div className="w-full">
            <span className="text-xs uppercase font-mono tracking-wider text-slate-400 block mb-4">
              Progressive Raster Reconstruction
            </span>

            {/* Dynamic N x N Grid of coalescing cells */}
            <div className="mx-auto my-2 p-2 rounded-lg bg-black/60 border border-white/10 w-48 h-48 flex items-center justify-center">
              <div
                className="grid gap-[1px] w-full h-full"
                style={{ gridTemplateColumns: `repeat(${rasterGrid.length}, minmax(0, 1fr))` }}
              >
                {rasterGrid.map((row, rIdx) =>
                  row.map((val, cIdx) => {
                    const intensity = Math.round(val * 255);
                    const hex = intensity.toString(16).padStart(2, '0');
                    const bg = `#${hex}${hex}${hex}`;
                    return (
                      <div
                        key={`raster-${rIdx}-${cIdx}`}
                        className="rounded-[1px]"
                        style={{ backgroundColor: bg }}
                      />
                    );
                  })
                )}
              </div>
            </div>
          </div>

          <div className="mt-4 space-y-1">
            <div className="text-xs font-mono text-cyan-300">
              Shot convergence: ε ∝ 1/√N
            </div>
            <div className="text-[11px] font-mono text-slate-500">
              Coalescing quantum image frame from projective readout counts
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StageTomography;
