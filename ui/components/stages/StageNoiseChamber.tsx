'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useQuantumStore } from '@/lib/quantumStore';

export const StageNoiseChamber: React.FC = () => {
  const statevector = useQuantumStore((state) => state.statevector);

  // Noise parameters (read-only NISQ chamber parameters)
  const noiseChannel = 'Depolarizing Quantum Channel';
  const noiseRate = 0.015; // Standard NISQ chamber rate p
  const purity = statevector ? statevector.purity : 1.0;

  // Determine noise severity badge color
  const getBadgeStyle = (p: number) => {
    if (p > 0.01) {
      return {
        label: 'High Noise (p > 0.01)',
        className: 'bg-[#f43f5e]/15 text-[#f43f5e] border-[#f43f5e]/30',
        dot: 'bg-[#f43f5e]',
      };
    }
    if (p > 0.001) {
      return {
        label: 'Moderate Noise (p > 0.001)',
        className: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
        dot: 'bg-amber-400',
      };
    }
    return {
      label: 'Low Noise (p ≤ 0.001)',
      className: 'bg-[#10b981]/15 text-[#10b981] border-[#10b981]/30',
      dot: 'bg-[#10b981]',
    };
  };

  const badge = getBadgeStyle(noiseRate);

  // Extract first 8 amplitude magnitudes |c_i|
  const amplitudes = statevector?.amplitudes && statevector.amplitudes.length > 0
    ? statevector.amplitudes.slice(0, 8)
    : [0.35, 0.42, 0.28, 0.15, 0.50, 0.22, 0.38, 0.18]; // visual baseline if awaiting stream

  const basisLabels = ['|000⟩', '|001⟩', '|010⟩', '|011⟩', '|100⟩', '|101⟩', '|110⟩', '|111⟩'];

  return (
    <div className="space-y-6">
      {/* Stage Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/10">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[#f43f5e]">Stage 03</span>
          <h2 className="text-2xl font-bold text-white tracking-tight">NISQ Environmental Noise Chamber</h2>
          <p className="text-sm text-slate-400 mt-1">
            Simulating decoherence, bit-flip, and depolarizing channels on density matrix state evolution.
          </p>
        </div>

        {/* Statevector Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-mono">
          <span
            className={`w-2 h-2 rounded-full ${
              statevector ? 'bg-[#00f5ff] animate-pulse' : 'bg-slate-500'
            }`}
          />
          <span className="text-slate-300">
            {statevector ? 'Density Matrix Updated' : 'Baseline State Prepared'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Noise Parameter Display (Read-Only) */}
        <div className="lg:col-span-6 space-y-6 bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#f43f5e]" />
              Channel Specifications
            </h3>
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono border ${badge.className}`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`} />
              {badge.label}
            </span>
          </div>

          <div className="space-y-4">
            <div className="bg-[#090a0f] border border-white/10 rounded-lg p-4 space-y-2">
              <div className="text-xs text-slate-400 uppercase font-mono">Noise Channel Model</div>
              <div className="text-base font-semibold text-white">{noiseChannel}</div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Applies isotropic Kraus operators: <span className="font-mono text-cyan-300">ε(ρ) = (1-p)ρ + (p/3)(XρX + YρY + ZρZ)</span> simulating uniform thermal decoherence.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-[#090a0f] border border-white/10 rounded-lg p-4">
                <span className="text-xs text-slate-400 font-mono block mb-1">Error Rate (p)</span>
                <span className="text-2xl font-bold font-mono text-[#f43f5e]">{noiseRate.toFixed(4)}</span>
                <span className="text-[11px] text-slate-500 block mt-1">Probability per gate</span>
              </div>
              <div className="bg-[#090a0f] border border-white/10 rounded-lg p-4">
                <span className="text-xs text-slate-400 font-mono block mb-1">Purity Level (γ)</span>
                <span className="text-2xl font-bold font-mono text-white">{purity.toFixed(4)}</span>
                <span className="text-[11px] text-slate-500 block mt-1">γ = 1.0 indicates pure state</span>
              </div>
            </div>

            {/* Purity Gauge (Horizontal bar colored green -> red) */}
            <div className="space-y-2 pt-2">
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-slate-300 font-semibold">State Purity γ = Tr(ρ²)</span>
                <span className="text-white font-bold">{Math.round(purity * 100)}%</span>
              </div>
              <div className="h-3 w-full rounded-full bg-white/10 p-[2px] overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.max(5, Math.min(100, purity * 100))}%` }}
                  transition={{ duration: 0.6, ease: 'easeOut' }}
                  className="h-full rounded-full bg-gradient-to-r from-[#f43f5e] via-amber-400 to-[#10b981]"
                />
              </div>
              <div className="flex justify-between text-[10px] font-mono text-slate-500">
                <span>0.0 (Maximally Mixed)</span>
                <span>0.5</span>
                <span>1.0 (Pure State)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Bloch Sphere Placeholder */}
        <div className="lg:col-span-6 bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6 flex flex-col items-center justify-center text-center">
          <div className="w-full flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Qubit Trajectory In State Space
            </span>
            <span className="text-xs font-mono text-[#00f5ff]">SU(2) Manifold</span>
          </div>

          <div className="relative my-4 flex items-center justify-center">
            {/* Ambient outer glow */}
            <div className="absolute w-56 h-56 rounded-full bg-[#00f5ff]/10 blur-xl pointer-events-none" />

            {/* Styled Circular Bloch Sphere Placeholder */}
            <div className="relative w-52 h-52 rounded-full bg-[#090a0f] border-2 border-[#00f5ff] shadow-[0_0_25px_rgba(0,245,255,0.3)] flex flex-col items-center justify-center p-4 overflow-hidden group">
              {/* Latitude & Longitude SVG rings */}
              <svg className="absolute inset-0 w-full h-full opacity-30 text-[#00f5ff]" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="0.5" strokeDasharray="2,2" />
                <ellipse cx="50" cy="50" rx="45" ry="16" fill="none" stroke="currentColor" strokeWidth="0.75" />
                <ellipse cx="50" cy="50" rx="16" ry="45" fill="none" stroke="currentColor" strokeWidth="0.75" />
                <line x1="50" y1="5" x2="50" y2="95" stroke="currentColor" strokeWidth="0.75" strokeDasharray="1,1" />
                <line x1="5" y1="50" x2="95" y2="50" stroke="currentColor" strokeWidth="0.75" strokeDasharray="1,1" />
              </svg>

              {/* State vector pointer line */}
              <motion.div
                animate={{ rotate: [0, 15, -10, 0] }}
                transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
                className="absolute w-24 h-[2px] bg-gradient-to-r from-transparent to-[#00f5ff] origin-left left-1/2 shadow-[0_0_8px_#00f5ff]"
              />

              <div className="relative z-10 space-y-1">
                <div className="text-sm font-bold text-white tracking-wide">3D Bloch Sphere</div>
                <div className="text-[11px] font-mono text-[#00f5ff]">(Three.js — Phase 3B Extension)</div>
              </div>
            </div>
          </div>

          <p className="text-xs text-slate-400 max-w-sm mt-1">
            Decoherence visualization loads with <code className="text-[#a855f7] font-mono">@react-three/fiber</code> canvas rendering real-time Bloch vector shrinkage under noise.
          </p>
        </div>
      </div>

      {/* Bottom: Statevector Amplitude Bars */}
      <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#00f5ff]" />
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
              Statevector Amplitude Magnitudes (|cᵢ|)
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {statevector ? 'First 8 Basis Coefficients' : 'Awaiting statevector updates...'}
          </span>
        </div>

        {/* Amplitude Flex Bar Chart */}
        <div className="grid grid-cols-4 sm:grid-cols-8 gap-3 pt-2">
          {amplitudes.map((amp, idx) => {
            const heightPercent = Math.max(8, Math.min(100, Math.round(Math.abs(amp) * 100)));
            return (
              <div key={idx} className="flex flex-col items-center gap-2">
                <div className="w-full h-32 bg-[#090a0f] border border-white/10 rounded-lg p-1.5 flex flex-col justify-end items-center relative overflow-hidden group">
                  {/* Amplitude value tooltip on hover */}
                  <span className="text-[10px] font-mono text-cyan-200 mb-1 z-10">
                    {amp.toFixed(2)}
                  </span>
                  <motion.div
                    key={`${idx}-${amp}`}
                    initial={{ height: 0 }}
                    animate={{ height: `${heightPercent}%` }}
                    transition={{ duration: 0.4, delay: idx * 0.04 }}
                    className="w-full bg-gradient-to-t from-cyan-600 to-[#00f5ff] rounded shadow-[0_0_8px_rgba(0,245,255,0.3)] group-hover:brightness-125 transition-all"
                  />
                </div>
                <span className="text-[11px] font-mono text-slate-400">
                  {basisLabels[idx] || `|${idx}⟩`}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default StageNoiseChamber;
