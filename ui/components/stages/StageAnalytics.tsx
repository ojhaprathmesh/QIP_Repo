'use client';

import React from 'react';
import { motion } from 'framer-motion';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import { useQuantumStore } from '@/lib/quantumStore';
import MetricCard from '@/components/shared/MetricCard';

// Mock sweep data across noise rates for PSNR comparison
const mockSweepData = [
  { pLabel: '10⁻⁴', p: 0.0001, frqi: 34.2, bm3d: 31.5 },
  { pLabel: '10⁻³', p: 0.001, frqi: 30.8, bm3d: 28.1 },
  { pLabel: '10⁻²', p: 0.01, frqi: 25.4, bm3d: 24.0 },
  { pLabel: '10⁻¹', p: 0.1, frqi: 18.2, bm3d: 19.8 },
];

export const StageAnalytics: React.FC = () => {
  const frameResult = useQuantumStore((state) => state.frameResult);
  const phaseCrit = useQuantumStore((state) => state.phaseCrit);

  const psnr = frameResult?.psnr !== undefined ? frameResult.psnr.toFixed(2) : '—';
  const ssim = frameResult?.ssim !== undefined ? frameResult.ssim.toFixed(4) : '—';
  const mse = frameResult?.mse !== undefined ? frameResult.mse.toFixed(5) : '—';

  const pCritVal = phaseCrit?.p_crit !== undefined && phaseCrit?.p_crit !== null
    ? phaseCrit.p_crit.toExponential(3)
    : null;

  const verdict = phaseCrit?.advantage_verdict || 'EVALUATING...';
  const isQuantum = verdict.toUpperCase().includes('QUANTUM');
  const isClassical = verdict.toUpperCase().includes('CLASSICAL');

  const pCritColorClass = isClassical
    ? 'text-[#f43f5e]' // coral
    : isQuantum
    ? 'text-[#00f5ff]' // cyan
    : 'text-slate-400';

  const verdictBadgeStyle = isQuantum
    ? 'bg-cyan-500/20 text-[#00f5ff] border-cyan-500/40 shadow-[0_0_12px_rgba(0,245,255,0.3)]'
    : isClassical
    ? 'bg-rose-500/20 text-[#f43f5e] border-rose-500/40 shadow-[0_0_12px_rgba(244,63,94,0.3)]'
    : 'bg-white/10 text-slate-300 border-white/20';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-xl border border-white/10 bg-white/5 backdrop-blur">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-[#10b981] animate-pulse" />
            <span className="text-xs font-mono uppercase tracking-wider text-emerald-400">
              Stage 06 // Comparative Evaluation & Analytics
            </span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Performance Benchmarks & Phase Transition
          </h2>
          <p className="text-sm text-slate-400 mt-0.5">
            Full-pipeline quality metrics, classical vs quantum advantage boundary, and scaling limits.
          </p>
        </div>

        {/* Animated Verdict Chip */}
        <motion.div
          animate={{ scale: [1, 1.04, 1] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          className={`px-4 py-2 rounded-full border text-xs md:text-sm font-mono font-bold tracking-wider uppercase text-center ${verdictBadgeStyle}`}
        >
          {verdict}
        </motion.div>
      </div>

      {/* Top Row: 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="PSNR Peak SNR"
          value={psnr}
          unit={frameResult ? 'dB' : undefined}
          color="cyan"
        />
        <MetricCard
          label="SSIM Structural"
          value={ssim}
          color="violet"
        />
        <MetricCard
          label="Mean Squared Error"
          value={mse}
          color="emerald"
        />
        <MetricCard
          label="State Fidelity"
          value="F = —"
          color="cyan"
        />
      </div>

      {/* Analytics Main Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Phase Transition Analysis Section */}
        <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs uppercase font-mono tracking-wider text-slate-400">
                Phase Transition Analysis
              </span>
              <span className="text-xs font-mono text-emerald-400">Threshold Search</span>
            </div>

            <div className="my-6 p-5 rounded-xl border border-white/10 bg-black/40 text-center space-y-3">
              <div className="text-xs font-mono uppercase tracking-widest text-slate-400">
                Critical Noise Boundary (p_crit)
              </div>
              <div className={`text-3xl md:text-4xl font-bold font-mono tracking-tight ${pCritColorClass}`}>
                {pCritVal ? `p* = ${pCritVal}` : 'p* = Undetermined'}
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Boundary where quantum advantage crosses below classical BM3D baseline
              </p>
            </div>

            <div className="space-y-3 border-t border-white/5 pt-4">
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-slate-400">Advantage Verdict:</span>
                <span className="font-semibold text-white">{verdict}</span>
              </div>
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-slate-400">Target Noise Channel:</span>
                <span className="text-slate-300">Depolarizing / Dephasing</span>
              </div>
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-slate-400">Classical Benchmark:</span>
                <span className="text-emerald-400">BM3D (Wavelet domain)</span>
              </div>
            </div>
          </div>

          <div className="text-[11px] font-mono text-slate-500 mt-6">
            Phase 4 sweeps identify the exact critical noise probability p_crit across channel topologies.
          </div>
        </div>

        {/* PSNR vs Noise Rate p Chart */}
        <div className="lg:col-span-2 rounded-xl border border-white/10 bg-white/5 backdrop-blur p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs uppercase font-mono tracking-wider text-slate-400">
                PSNR vs. Noise Rate p (Phase Transition Curve)
              </span>
              <span className="text-xs font-mono text-slate-400">Log-scale p</span>
            </div>

            <div className="h-64 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={mockSweepData} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                  <XAxis
                    dataKey="pLabel"
                    stroke="#64748b"
                    fontSize={12}
                    tickLine={false}
                    label={{ value: 'Noise Rate p', position: 'insideBottom', offset: -5, fill: '#64748b', fontSize: 11 }}
                  />
                  <YAxis
                    stroke="#64748b"
                    fontSize={12}
                    tickLine={false}
                    domain={[15, 38]}
                    label={{ value: 'PSNR (dB)', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#090a0f',
                      borderColor: 'rgba(255,255,255,0.15)',
                      borderRadius: '8px',
                      fontSize: '12px',
                      fontFamily: 'monospace',
                    }}
                  />
                  <Legend
                    wrapperStyle={{ paddingTop: '10px', fontSize: '12px', fontFamily: 'monospace' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="frqi"
                    name="FRQI (Quantum)"
                    stroke="#00f5ff"
                    strokeWidth={2.5}
                    dot={{ fill: '#00f5ff', r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="bm3d"
                    name="Classical BM3D"
                    stroke="#10b981"
                    strokeWidth={2}
                    strokeDasharray="4 4"
                    dot={{ fill: '#10b981', r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="text-[11px] font-mono text-slate-500 mt-2">
            Simulated parametric sweep. Live phase transition boundary dynamically calculated during sweep executions.
          </div>
        </div>
      </div>
    </div>
  );
};

export default StageAnalytics;
