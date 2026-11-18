'use client';

import React, { useState, useMemo, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useQuantumStore } from '@/lib/quantumStore';

export const StageIngestion: React.FC = () => {
  const initial = useQuantumStore.getState().config;
  const setConfig = useQuantumStore((s) => s.setConfig);
  const [resolution, setResolution] = useState<number>(initial.resolution);
  const [pattern, setPattern] = useState<'checkerboard' | 'gradient' | 'shepp_logan'>(
    initial.pattern as 'checkerboard' | 'gradient' | 'shepp_logan'
  );
  const [noiseEnabled, setNoiseEnabled] = useState<boolean>(initial.noise_rate > 0.005);
  const [noiseSigma, setNoiseSigma] = useState<number>(Math.max(0.08, initial.noise_rate * 4));

  // Publish the user's ingestion choices so "Run Simulation" uses them.
  useEffect(() => {
    setConfig({
      resolution,
      pattern,
      noise_rate: noiseEnabled ? noiseSigma / 4 : 0.001,
    });
  }, [resolution, pattern, noiseEnabled, noiseSigma, setConfig]);

  // Resolution n calculation: N = 2^n -> n = log2(resolution)
  const n = useMemo(() => Math.round(Math.log2(resolution)), [resolution]);
  const frqiQubits = 2 * n + 1;
  const neqrQubits = 2 * n + 8; // assuming 8-bit grayscale (q = 8)

  // Generate grid pixel intensities (0 to 1)
  const displayResolution = Math.min(resolution, 16); // limit visual grid to 16 for clean UI rendering
  const gridPixels = useMemo(() => {
    const rows: number[][] = [];
    for (let r = 0; r < displayResolution; r++) {
      const row: number[] = [];
      for (let c = 0; c < displayResolution; c++) {
        let val = 0;
        if (pattern === 'checkerboard') {
          val = (r + c) % 2 === 0 ? 0.92 : 0.08;
        } else if (pattern === 'gradient') {
          val = (r + c) / (2 * (displayResolution - 1));
        } else if (pattern === 'shepp_logan') {
          // Synthetic phantom-like intensity
          const cx = displayResolution / 2;
          const cy = displayResolution / 2;
          const dist = Math.sqrt((r - cx) ** 2 + (c - cy) ** 2) / (displayResolution / 2);
          if (dist < 0.25) val = 0.95;
          else if (dist < 0.5) val = 0.45;
          else if (dist < 0.8) val = 0.75;
          else if (dist < 1.0) val = 0.25;
          else val = 0.05;
        }

        // Apply noise if enabled
        if (noiseEnabled) {
          const pseudoNoise = (Math.sin(r * 997 + c * 331) * 0.5 + 0.5 - 0.5) * noiseSigma * 3;
          val = Math.max(0, Math.min(1, val + pseudoNoise));
        }

        row.push(val);
      }
      rows.push(row);
    }
    return rows;
  }, [displayResolution, pattern, noiseEnabled, noiseSigma]);

  return (
    <div className="space-y-6">
      {/* Top Banner / Stage Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/10">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[#00f5ff]">Stage 01</span>
          <h2 className="text-2xl font-bold text-white tracking-tight">Image Ingestion & Preprocessing</h2>
          <p className="text-sm text-slate-400 mt-1">
            Classical image preparation, spatial discretization, and quantum qubit requirement mapping.
          </p>
        </div>

        {/* Live Qubit Requirements Display */}
        <div className="flex items-center gap-3 bg-[#090a0f] border border-[#00f5ff]/30 px-4 py-2.5 rounded-lg shadow-[0_0_15px_rgba(0,245,255,0.1)]">
          <div className="text-xs font-mono text-slate-300">
            <span className="text-slate-400">Scale:</span> <span className="text-white font-bold">{resolution}×{resolution}</span> (n={n})
          </div>
          <div className="h-4 w-[1px] bg-white/20" />
          <div className="text-xs font-mono">
            <span className="text-[#00f5ff] font-semibold">FRQI:</span> 2n+1 = <span className="text-white font-bold">{frqiQubits}</span> qubits
          </div>
          <div className="h-4 w-[1px] bg-white/20" />
          <div className="text-xs font-mono">
            <span className="text-[#a855f7] font-semibold">NEQR:</span> 2n+q = <span className="text-white font-bold">{neqrQubits}</span> qubits
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Interactive Controls */}
        <div className="lg:col-span-5 space-y-5 bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#00f5ff]" />
            Preprocessing Parameters
          </h3>

          {/* Resolution Selector */}
          <div>
            <label className="text-xs text-slate-400 font-medium block mb-2">Resolution (N × N)</label>
            <div className="grid grid-cols-4 gap-2">
              {[4, 8, 16, 32].map((res) => (
                <button
                  key={res}
                  onClick={() => setResolution(res)}
                  className={`py-2 px-3 rounded-lg text-xs font-mono font-medium transition-all duration-200 border ${
                    resolution === res
                      ? 'bg-[#00f5ff]/20 text-[#00f5ff] border-[#00f5ff] shadow-[0_0_10px_rgba(0,245,255,0.2)]'
                      : 'bg-white/5 text-slate-400 border-white/10 hover:border-white/25 hover:text-white'
                  }`}
                >
                  {res}×{res}
                </button>
              ))}
            </div>
            {resolution > 16 && (
              <p className="text-[11px] text-amber-400/80 mt-1.5 font-mono">
                * Viewport downsamples preview grid to 16×16 for responsive rendering.
              </p>
            )}
          </div>

          {/* Pattern Selector */}
          <div>
            <label className="text-xs text-slate-400 font-medium block mb-2">Synthetic Pattern</label>
            <div className="grid grid-cols-3 gap-2">
              {(['checkerboard', 'gradient', 'shepp_logan'] as const).map((pat) => (
                <button
                  key={pat}
                  onClick={() => setPattern(pat)}
                  className={`py-2 px-2 rounded-lg text-xs font-medium capitalize transition-all duration-200 border truncate ${
                    pattern === pat
                      ? 'bg-[#a855f7]/20 text-[#a855f7] border-[#a855f7] shadow-[0_0_10px_rgba(168,85,247,0.2)]'
                      : 'bg-white/5 text-slate-400 border-white/10 hover:border-white/25 hover:text-white'
                  }`}
                >
                  {pat.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>

          {/* Noise Injection Toggle & Slider */}
          <div className="pt-3 border-t border-white/10 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-300 font-medium">Inject Synthetic Noise</span>
              <button
                type="button"
                onClick={() => setNoiseEnabled(!noiseEnabled)}
                className={`w-11 h-6 flex items-center rounded-full p-1 cursor-pointer transition-colors duration-200 ${
                  noiseEnabled ? 'bg-[#f43f5e]' : 'bg-white/10'
                }`}
              >
                <div
                  className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform duration-200 ${
                    noiseEnabled ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>

            {noiseEnabled && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-2 pt-1"
              >
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-400">Noise Intensity (σ):</span>
                  <span className="text-[#f43f5e] font-semibold">{noiseSigma.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.01"
                  max="0.4"
                  step="0.01"
                  value={noiseSigma}
                  onChange={(e) => setNoiseSigma(parseFloat(e.target.value))}
                  className="w-full accent-[#f43f5e] bg-white/10 h-1.5 rounded-lg appearance-none cursor-pointer"
                />
              </motion.div>
            )}
          </div>

          {/* Mathematical Mapping Card */}
          <div className="bg-[#090a0f]/80 border border-white/10 rounded-lg p-3 text-xs font-mono space-y-1.5">
            <div className="text-slate-400 font-semibold uppercase text-[10px] tracking-wider">Spatial Encoding Specs</div>
            <div className="flex justify-between text-slate-300">
              <span>Pixel Count (N²):</span>
              <span className="text-white font-bold">{resolution * resolution}</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Address Qubits (2n):</span>
              <span className="text-[#00f5ff]">{2 * n}</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Color / Phase Ancilla:</span>
              <span className="text-[#a855f7]">{pattern === 'shepp_logan' ? '1 (FRQI)' : '8 (NEQR)'}</span>
            </div>
          </div>
        </div>

        {/* Right: Grid Visualization */}
        <div className="lg:col-span-7 bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6 flex flex-col items-center justify-center">
          <div className="w-full flex items-center justify-between mb-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Pixel Grid Buffer ({displayResolution}×{displayResolution})
            </span>
            <span className="text-xs font-mono text-slate-500">
              Intensity Range: [0.00, 1.00]
            </span>
          </div>

          <div className="relative p-3 rounded-xl bg-[#090a0f] border border-white/10 shadow-[0_0_30px_rgba(0,0,0,0.5)]">
            <motion.div
              key={`${pattern}-${resolution}-${noiseEnabled}-${noiseSigma}`}
              initial="hidden"
              animate="visible"
              variants={{
                hidden: { opacity: 0 },
                visible: {
                  opacity: 1,
                  transition: {
                    staggerChildren: 0.003,
                  },
                },
              }}
              className="grid gap-[2px]"
              style={{
                gridTemplateColumns: `repeat(${displayResolution}, minmax(0, 1fr))`,
                width: displayResolution <= 8 ? '256px' : '320px',
                height: displayResolution <= 8 ? '256px' : '320px',
              }}
            >
              {gridPixels.map((row, rIdx) =>
                row.map((val, cIdx) => (
                  <motion.div
                    key={`${rIdx}-${cIdx}`}
                    variants={{
                      hidden: { opacity: 0, scale: 0.8 },
                      visible: { opacity: 1, scale: 1 },
                    }}
                    transition={{ duration: 0.15 }}
                    className="relative group rounded-[2px] transition-colors"
                    style={{
                      backgroundColor: `rgb(${Math.round(val * 255)}, ${Math.round(val * 255)}, ${Math.round(
                        val * 255
                      )})`,
                    }}
                    title={`(${rIdx}, ${cIdx}): ${val.toFixed(2)}`}
                  >
                    <div className="opacity-0 group-hover:opacity-100 absolute inset-0 bg-[#00f5ff]/40 pointer-events-none rounded-[2px]" />
                  </motion.div>
                ))
              )}
            </motion.div>
          </div>

          <div className="mt-4 flex items-center gap-4 text-xs text-slate-400">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 bg-black rounded border border-white/20" />
              <span>0.00 (Black)</span>
            </div>
            <div className="w-16 h-2 bg-gradient-to-r from-black via-slate-500 to-white rounded" />
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 bg-white rounded border border-white/20" />
              <span>1.00 (White)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StageIngestion;
