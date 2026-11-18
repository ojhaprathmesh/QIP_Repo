'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useQuantumStore } from '@/lib/quantumStore';
import { MetricCard } from '@/components/shared/MetricCard';

export const StageEncoding: React.FC = () => {
  const circuitInfo = useQuantumStore((state) => state.circuitInfo);

  // If circuitInfo is present, calculate comparative depth/qubit metrics
  const activeQubits = circuitInfo?.qubits ?? 0;
  const activeDepth = circuitInfo?.depth ?? 0;
  const activeGates = circuitInfo?.total_gates ?? 0;
  const activeCnot = circuitInfo?.cnot_count ?? 0;

  // Max scale references for visual gauges
  const maxQubitsGauge = 16;
  const maxDepthGauge = 200;

  return (
    <div className="space-y-6">
      {/* Stage Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/10">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[#a855f7]">Stage 02</span>
          <h2 className="text-2xl font-bold text-white tracking-tight">Quantum State Synthesis & Encoding</h2>
          <p className="text-sm text-slate-400 mt-1">
            Mapping pixel intensity values to state space via continuous rotations (FRQI) or basis states (NEQR).
          </p>
        </div>

        {/* Status Indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-mono">
          <span
            className={`w-2 h-2 rounded-full ${
              circuitInfo ? 'bg-[#10b981] animate-pulse' : 'bg-slate-500'
            }`}
          />
          <span className="text-slate-300">
            {circuitInfo ? 'Circuit Compiled' : 'Waiting for Compiler'}
          </span>
        </div>
      </div>

      {/* Dimmed Waiting State Banner if circuitInfo is null */}
      {!circuitInfo && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="rounded-xl border border-dashed border-white/15 bg-white/[0.02] p-8 text-center backdrop-blur-sm"
        >
          <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <svg className="w-6 h-6 animate-spin text-[#00f5ff]" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          </div>
          <h3 className="text-base font-semibold text-white">Awaiting circuit compilation...</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
            Initiate a simulation stream to synthesize the quantum circuit gates and extract depth benchmarks.
          </p>
        </motion.div>
      )}

      {/* Side-by-Side Encoding Comparison Panels */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left: FRQI Panel (Cyan) */}
        <motion.div
          initial={{ opacity: 0, x: -15 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
          className={`relative rounded-xl bg-white/5 backdrop-blur-md border border-[#00f5ff]/30 p-6 flex flex-col justify-between transition-all duration-300 shadow-[0_0_20px_rgba(0,245,255,0.05)] ${
            !circuitInfo ? 'opacity-70' : ''
          }`}
        >
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] font-mono tracking-widest text-[#00f5ff] uppercase block">
                  Phase / Amplitude Encoding
                </span>
                <h3 className="text-lg font-bold text-white">FRQI Representation</h3>
              </div>
              <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-[#00f5ff]/15 text-[#00f5ff] border border-[#00f5ff]/30">
                2n + 1 Qubits
              </span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Flexible Representation of Quantum Images encodes classical intensities as angles in single-qubit rotations
              entangled with address state registers.
            </p>

            {/* Formula Block */}
            <div className="rounded-lg bg-[#090a0f] border border-[#00f5ff]/20 p-3 text-center overflow-x-auto">
              <span className="text-xs font-mono text-[#00f5ff] whitespace-nowrap">
                |I_FRQI⟩ = 1/2ⁿ Σᵢ (cosθᵢ|0⟩ + sinθᵢ|1⟩)|i⟩
              </span>
            </div>

            {/* Depth Gauge */}
            <div className="space-y-1.5 pt-2">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-slate-400">Relative Circuit Depth:</span>
                <span className="text-[#00f5ff] font-semibold">
                  {circuitInfo ? `${activeDepth} Gates` : 'O(2²ⁿ) asymptotic'}
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-white/10 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{
                    width: circuitInfo
                      ? `${Math.min(100, Math.round((activeDepth / maxDepthGauge) * 100))}%`
                      : '35%',
                  }}
                  transition={{ duration: 0.6, ease: 'easeOut' }}
                  className="h-full bg-gradient-to-r from-cyan-500 to-[#00f5ff] rounded-full"
                />
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-white/10 flex items-center justify-between text-xs text-slate-400">
            <span>Ancilla Register: 1 qubit</span>
            <span className="text-emerald-400 font-mono">High Fidelity Compression</span>
          </div>
        </motion.div>

        {/* Right: NEQR Panel (Violet) */}
        <motion.div
          initial={{ opacity: 0, x: 15 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
          className={`relative rounded-xl bg-white/5 backdrop-blur-md border border-[#a855f7]/30 p-6 flex flex-col justify-between transition-all duration-300 shadow-[0_0_20px_rgba(168,85,247,0.05)] ${
            !circuitInfo ? 'opacity-70' : ''
          }`}
        >
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] font-mono tracking-widest text-[#a855f7] uppercase block">
                  Computational Basis Encoding
                </span>
                <h3 className="text-lg font-bold text-white">NEQR Representation</h3>
              </div>
              <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-[#a855f7]/15 text-[#a855f7] border border-[#a855f7]/30">
                2n + q Qubits
              </span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Novel Enhanced Quantum Representation stores pixel gray values directly into basis states |C(i)⟩ of a
              q-qubit string, enabling exact classical arithmetic and bit-level transformations.
            </p>

            {/* Formula Block */}
            <div className="rounded-lg bg-[#090a0f] border border-[#a855f7]/20 p-3 text-center overflow-x-auto">
              <span className="text-xs font-mono text-[#a855f7] whitespace-nowrap">
                |I_NEQR⟩ = 1/2ⁿ Σᵢ |C(i)⟩|i⟩
              </span>
            </div>

            {/* Depth Gauge */}
            <div className="space-y-1.5 pt-2">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-slate-400">Relative Circuit Depth:</span>
                <span className="text-[#a855f7] font-semibold">
                  {circuitInfo ? `${Math.round(activeDepth * 1.4)} Gates (Est)` : 'O(q · 2²ⁿ) gates'}
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-white/10 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{
                    width: circuitInfo
                      ? `${Math.min(100, Math.round(((activeDepth * 1.4) / maxDepthGauge) * 100))}%`
                      : '55%',
                  }}
                  transition={{ duration: 0.6, ease: 'easeOut' }}
                  className="h-full bg-gradient-to-r from-purple-500 to-[#a855f7] rounded-full"
                />
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-white/10 flex items-center justify-between text-xs text-slate-400">
            <span>Color Register: 8 qubits</span>
            <span className="text-[#a855f7] font-mono">Direct Measurement Access</span>
          </div>
        </motion.div>
      </div>

      {/* 4 MetricCards Below */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Total Qubits"
          value={circuitInfo ? activeQubits : '—'}
          color="cyan"
          unit={circuitInfo ? 'q' : undefined}
        />
        <MetricCard
          label="Circuit Depth"
          value={circuitInfo ? activeDepth : '—'}
          color="violet"
          unit={circuitInfo ? 'layers' : undefined}
        />
        <MetricCard
          label="Total Gates"
          value={circuitInfo ? activeGates : '—'}
          color="emerald"
          unit={circuitInfo ? 'ops' : undefined}
        />
        <MetricCard
          label="CNOT Entanglers"
          value={circuitInfo ? activeCnot : '—'}
          color="coral"
          unit={circuitInfo ? 'cx' : undefined}
        />
      </div>
    </div>
  );
};

export default StageEncoding;
