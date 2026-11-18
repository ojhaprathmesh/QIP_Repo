'use client';

import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { RotateCcw } from 'lucide-react';
import { useQuantumStore } from '@/lib/quantumStore';

interface BlochPoint3D {
  x: number;
  y: number;
  z: number;
}

export const StageNoiseChamber: React.FC = () => {
  const statevector = useQuantumStore((state) => state.statevector);
  const configuredNoiseRate = useQuantumStore((state) => state.config.noise_rate);
  const encoding = useQuantumStore((state) => state.config.encoding);

  // Noise parameters reflecting the user's configured NISQ chamber rate p
  const noiseChannel = 'Depolarizing + Thermal (T₁/T₂) Kraus Channel';
  const noiseRate = configuredNoiseRate ?? 0.003;
  const purity = statevector ? statevector.purity : 1.0;

  // Extract first 8 amplitude magnitudes |c_i|
  const amplitudes =
    statevector?.amplitudes && statevector.amplitudes.length > 0
      ? statevector.amplitudes.slice(0, 8)
      : [0.35, 0.42, 0.28, 0.15, 0.5, 0.22, 0.38, 0.18];

  const basisLabels = ['|000⟩', '|001⟩', '|010⟩', '|011⟩', '|100⟩', '|101⟩', '|110⟩', '|111⟩'];

  // Compute live Bloch vector components (rx, ry, rz) from purity & statevector amplitudes:
  // For a single-qubit reduced density matrix rho = 1/2 (I + r . sigma), Tr(rho^2) = 1/2 (1 + |r|^2)
  // => Bloch radius |r| = sqrt(max(0, 2 * purity - 1)).
  const blochRadius = Math.sqrt(Math.max(0.02, Math.min(1.0, 2 * purity - 1)));
  const a0 = amplitudes[0] ?? 0.35;
  const a1 = amplitudes[1] ?? 0.42;
  const a2 = amplitudes[2] ?? 0.28;
  const a3 = amplitudes[3] ?? 0.15;
  const norm01 = Math.max(1e-5, Math.hypot(a0, a1));
  const theta = 2 * Math.acos(Math.min(1, Math.max(0, a0 / norm01)));
  const phi = ((a2 - a3) * Math.PI * 3.2) + (1 - purity) * Math.PI * 2.5;

  const rx = blochRadius * Math.sin(theta) * Math.cos(phi);
  const ry = blochRadius * Math.sin(theta) * Math.sin(phi);
  const rz = blochRadius * Math.cos(theta);

  // 3D interactive orbit state & decoherence trajectory history
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [autoOrbit, setAutoOrbit] = useState<boolean>(true);
  const rotRef = useRef<{ yaw: number; pitch: number }>({ yaw: -0.62, pitch: 0.38 });
  const dragRef = useRef<{ active: boolean; lastX: number; lastY: number }>({
    active: false,
    lastX: 0,
    lastY: 0,
  });
  const trailRef = useRef<BlochPoint3D[]>([]);
  const targetVecRef = useRef<BlochPoint3D>({ x: rx, y: ry, z: rz });
  const currentVecRef = useRef<BlochPoint3D>({ x: rx, y: ry, z: rz });
  const purityRef = useRef<number>(purity);

  // Record trajectory points whenever statevector updates
  useEffect(() => {
    targetVecRef.current = { x: rx, y: ry, z: rz };
    purityRef.current = purity;
    const trail = trailRef.current;
    const last = trail[trail.length - 1];
    if (!last || Math.hypot(last.x - rx, last.y - ry, last.z - rz) > 0.015) {
      trail.push({ x: rx, y: ry, z: rz });
      if (trail.length > 36) trail.shift();
    }
  }, [rx, ry, rz, purity]);

  // Reset trail when purity returns to 1.0
  useEffect(() => {
    if (purity >= 0.999) {
      trailRef.current = [{ x: rx, y: ry, z: rz }];
    }
  }, [purity, rx, ry, rz]);

  // 60 FPS 3D Bloch Sphere Canvas Renderer
  useEffect(() => {
    let rafId = 0;

    const renderLoop = () => {
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext('2d');
        if (ctx) {
          const dpr = window.devicePixelRatio || 1;
          const width = 300;
          const height = 300;
          if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
            canvas.width = width * dpr;
            canvas.height = height * dpr;
          }
          ctx.save();
          ctx.scale(dpr, dpr);
          ctx.clearRect(0, 0, width, height);

          if (autoOrbit && !dragRef.current.active) {
            rotRef.current.yaw += 0.008;
          }

          // Smoothly interpolate current Bloch vector toward target
          const cur = currentVecRef.current;
          const tgt = targetVecRef.current;
          cur.x += (tgt.x - cur.x) * 0.14;
          cur.y += (tgt.y - cur.y) * 0.14;
          cur.z += (tgt.z - cur.z) * 0.14;

          const cx = width / 2;
          const cy = height / 2;
          const R = 108;
          const yaw = rotRef.current.yaw;
          const pitch = rotRef.current.pitch;
          const cosY = Math.cos(yaw);
          const sinY = Math.sin(yaw);
          const cosP = Math.cos(pitch);
          const sinP = Math.sin(pitch);

          // Project 3D Bloch coordinates (x, y, z in [-1, 1], where z is vertical |0> -> |1> axis)
          const project = (bx: number, by: number, bz: number) => {
            // Map Bloch (bx, by, bz) -> 3D view space (X=bx, Y=-bz, Z=by)
            const x1 = bx * cosY - by * sinY;
            const z1 = bx * sinY + by * cosY;
            const y1 = -bz;
            const y2 = y1 * cosP - z1 * sinP;
            const z2 = y1 * sinP + z1 * cosP;
            const perspective = 3.4 / (3.4 + z2 * 0.45);
            return {
              px: cx + x1 * R * perspective,
              py: cy + y2 * R * perspective,
              depth: z2,
              scale: perspective,
            };
          };

          // 1. Outer sphere ambient glow & shaded background disc
          const bgGrad = ctx.createRadialGradient(cx - 24, cy - 28, 12, cx, cy, R);
          bgGrad.addColorStop(0, 'rgba(0, 245, 255, 0.10)');
          bgGrad.addColorStop(0.65, 'rgba(15, 23, 42, 0.65)');
          bgGrad.addColorStop(1, 'rgba(9, 10, 15, 0.95)');
          ctx.beginPath();
          ctx.arc(cx, cy, R, 0, Math.PI * 2);
          ctx.fillStyle = bgGrad;
          ctx.fill();
          ctx.lineWidth = 1.4;
          ctx.strokeStyle = 'rgba(0, 245, 255, 0.45)';
          ctx.stroke();

          // 2. Inner contracted Purity Shell (radius = |r| = sqrt(2*purity - 1))
          const curRadius = Math.min(1, Math.hypot(cur.x, cur.y, cur.z));
          if (curRadius < 0.98) {
            ctx.beginPath();
            ctx.arc(cx, cy, R * curRadius, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(168, 85, 247, 0.08)';
            ctx.fill();
            ctx.setLineDash([3, 3]);
            ctx.lineWidth = 1.1;
            ctx.strokeStyle = 'rgba(168, 85, 247, 0.55)';
            ctx.stroke();
            ctx.setLineDash([]);
          }

          // Helper to draw a 3D circle on the unit sphere
          const drawRing3D = (
            pointFn: (t: number) => [number, number, number],
            frontColor: string,
            backColor: string,
            lineWidth = 1.0
          ) => {
            const steps = 64;
            for (let i = 0; i < steps; i++) {
              const t0 = (i / steps) * Math.PI * 2;
              const t1 = ((i + 1) / steps) * Math.PI * 2;
              const [x0, y0, z0] = pointFn(t0);
              const [x1, y1, z1] = pointFn(t1);
              const p0 = project(x0, y0, z0);
              const p1 = project(x1, y1, z1);
              ctx.beginPath();
              ctx.moveTo(p0.px, p0.py);
              ctx.lineTo(p1.px, p1.py);
              ctx.lineWidth = lineWidth;
              ctx.strokeStyle = p0.depth < 0 ? frontColor : backColor;
              ctx.stroke();
            }
          };

          // 3. Latitude & Longitude Wireframe Meridians
          // Equator (z = 0)
          drawRing3D(
            (t) => [Math.cos(t), Math.sin(t), 0],
            'rgba(0, 245, 255, 0.55)',
            'rgba(0, 245, 255, 0.16)',
            1.2
          );
          // XZ Meridian (y = 0)
          drawRing3D(
            (t) => [Math.cos(t), 0, Math.sin(t)],
            'rgba(148, 163, 184, 0.38)',
            'rgba(148, 163, 184, 0.12)',
            0.9
          );
          // YZ Meridian (x = 0)
          drawRing3D(
            (t) => [0, Math.cos(t), Math.sin(t)],
            'rgba(148, 163, 184, 0.38)',
            'rgba(148, 163, 184, 0.12)',
            0.9
          );
          // Tropics (z = ±0.5)
          drawRing3D(
            (t) => [Math.cos(t) * 0.866, Math.sin(t) * 0.866, 0.5],
            'rgba(0, 245, 255, 0.20)',
            'rgba(0, 245, 255, 0.07)',
            0.7
          );
          drawRing3D(
            (t) => [Math.cos(t) * 0.866, Math.sin(t) * 0.866, -0.5],
            'rgba(0, 245, 255, 0.20)',
            'rgba(0, 245, 255, 0.07)',
            0.7
          );

          // 4. Orthogonal X, Y, Z Axes & Basis Labels
          const axes: {
            from: [number, number, number];
            to: [number, number, number];
            posLabel: string;
            negLabel: string;
            color: string;
          }[] = [
            { from: [0, 0, -1], to: [0, 0, 1], posLabel: '|0⟩', negLabel: '|1⟩', color: 'rgba(226, 232, 240, 0.55)' },
            { from: [-1, 0, 0], to: [1, 0, 0], posLabel: '|+⟩', negLabel: '|−⟩', color: 'rgba(0, 245, 255, 0.45)' },
            { from: [0, -1, 0], to: [0, 1, 0], posLabel: '|+i⟩', negLabel: '|−i⟩', color: 'rgba(168, 85, 247, 0.45)' },
          ];

          ctx.font = 'bold 11px ui-monospace, SFMono-Regular, Menlo, monospace';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';

          for (const ax of axes) {
            const pFrom = project(...ax.from);
            const pTo = project(...ax.to);
            ctx.beginPath();
            ctx.setLineDash([2, 3]);
            ctx.moveTo(pFrom.px, pFrom.py);
            ctx.lineTo(pTo.px, pTo.py);
            ctx.strokeStyle = ax.color;
            ctx.lineWidth = 1;
            ctx.stroke();
            ctx.setLineDash([]);

            const lblPos = project(ax.to[0] * 1.16, ax.to[1] * 1.16, ax.to[2] * 1.16);
            const lblNeg = project(ax.from[0] * 1.16, ax.from[1] * 1.16, ax.from[2] * 1.16);
            ctx.fillStyle = '#e2e8f0';
            ctx.fillText(ax.posLabel, lblPos.px, lblPos.py);
            ctx.fillStyle = '#94a3b8';
            ctx.fillText(ax.negLabel, lblNeg.px, lblNeg.py);
          }

          // 5. Decoherence Trajectory Trail in 3D
          const trail = trailRef.current;
          if (trail.length > 1) {
            for (let i = 1; i < trail.length; i++) {
              const p0 = project(trail[i - 1].x, trail[i - 1].y, trail[i - 1].z);
              const p1 = project(trail[i].x, trail[i].y, trail[i].z);
              const alpha = (i / trail.length) * 0.75;
              ctx.beginPath();
              ctx.moveTo(p0.px, p0.py);
              ctx.lineTo(p1.px, p1.py);
              ctx.strokeStyle = `rgba(168, 85, 247, ${alpha.toFixed(3)})`;
              ctx.lineWidth = 2;
              ctx.stroke();
            }
          }

          // 6. Equatorial Projection Drop-Line (helps visually gauge 3D depth)
          const origin = project(0, 0, 0);
          const eqProj = project(cur.x, cur.y, 0);
          const tip = project(cur.x, cur.y, cur.z);

          ctx.beginPath();
          ctx.setLineDash([2, 2]);
          ctx.moveTo(origin.px, origin.py);
          ctx.lineTo(eqProj.px, eqProj.py);
          ctx.lineTo(tip.px, tip.py);
          ctx.strokeStyle = 'rgba(0, 245, 255, 0.35)';
          ctx.lineWidth = 1;
          ctx.stroke();
          ctx.setLineDash([]);

          // 7. Live 3D Bloch State Vector Arrow (color shifts cyan -> amber -> coral as purity drops)
          const vecColor =
            purityRef.current > 0.82
              ? '#00f5ff'
              : purityRef.current > 0.55
              ? '#f59e0b'
              : '#f43f5e';

          ctx.beginPath();
          ctx.moveTo(origin.px, origin.py);
          ctx.lineTo(tip.px, tip.py);
          ctx.strokeStyle = vecColor;
          ctx.lineWidth = 3;
          ctx.shadowColor = vecColor;
          ctx.shadowBlur = 12;
          ctx.stroke();

          // Glowing tip sphere
          ctx.beginPath();
          ctx.arc(tip.px, tip.py, 5.5 * tip.scale, 0, Math.PI * 2);
          ctx.fillStyle = '#ffffff';
          ctx.fill();
          ctx.lineWidth = 2.5;
          ctx.strokeStyle = vecColor;
          ctx.stroke();
          ctx.shadowBlur = 0;

          // Maximally mixed origin marker
          ctx.beginPath();
          ctx.arc(origin.px, origin.py, 3, 0, Math.PI * 2);
          ctx.fillStyle = '#94a3b8';
          ctx.fill();

          ctx.restore();
        }
      }
      rafId = requestAnimationFrame(renderLoop);
    };

    rafId = requestAnimationFrame(renderLoop);
    return () => cancelAnimationFrame(rafId);
  }, [autoOrbit]);

  // Determine noise severity badge color
  const getBadgeStyle = (p: number) => {
    if (p >= 0.008) {
      return {
        label: 'Super-Critical Noise (p ≥ p_crit)',
        className: 'bg-[#f43f5e]/15 text-[#f43f5e] border-[#f43f5e]/30',
        dot: 'bg-[#f43f5e]',
      };
    }
    if (p >= 0.005) {
      return {
        label: 'Near-Horizon Noise (p ≈ p_crit)',
        className: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
        dot: 'bg-amber-400',
      };
    }
    return {
      label: 'Sub-Critical NISQ (p < p_crit)',
      className: 'bg-[#10b981]/15 text-[#10b981] border-[#10b981]/30',
      dot: 'bg-[#10b981]',
    };
  };

  const badge = getBadgeStyle(noiseRate);

  return (
    <div className="space-y-6">
      {/* Stage Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/10">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[#f43f5e]">Stage 03</span>
          <h2 className="text-2xl font-bold text-white tracking-tight">NISQ Noise Chamber & Decoherence</h2>
          <p className="text-sm text-slate-400 mt-1">
            Simulating non-unitary open quantum system evolution via Kraus operators and environmental coupling.
          </p>
        </div>

        {/* Dynamic Noise Severity Badge */}
        <div className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full border text-xs font-mono font-semibold ${badge.className}`}>
          <span className={`w-2 h-2 rounded-full ${badge.dot} animate-pulse`} />
          <span>{badge.label}</span>
        </div>
      </div>

      {/* Main Content Split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Kraus Noise Telemetry & Purity Gauge */}
        <div className="lg:col-span-6 bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6 flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#f43f5e]" />
              Noise Channel Telemetry ({encoding.toUpperCase()})
            </h3>

            {/* Operator Formula Block */}
            <div className="rounded-lg bg-[#090a0f] border border-white/10 p-3.5 space-y-1.5">
              <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                Kraus Operator Sum Representation
              </div>
              <div className="text-sm font-mono text-[#00f5ff] tracking-wide">
                ℰ(ρ) = Σₖ Eₖ ρ Eₖ† ,   Σₖ Eₖ† Eₖ = I
              </div>
            </div>

            {/* Active Channel Info Grid */}
            <div className="grid grid-cols-2 gap-3 pt-1">
              <div className="bg-[#090a0f] border border-white/10 rounded-lg p-3.5 col-span-2">
                <span className="text-xs text-slate-400 font-mono block mb-0.5">Active Quantum Channel</span>
                <span className="text-sm font-bold text-white">{noiseChannel}</span>
              </div>
              <div className="bg-[#090a0f] border border-white/10 rounded-lg p-4">
                <span className="text-xs text-slate-400 font-mono block mb-1">Gate Error Rate (p)</span>
                <span className="text-2xl font-bold font-mono text-[#f43f5e]">{noiseRate.toFixed(4)}</span>
                <span className="text-[11px] text-slate-500 block mt-1">Depolarizing probability / gate</span>
              </div>
              <div className="bg-[#090a0f] border border-white/10 rounded-lg p-4">
                <span className="text-xs text-slate-400 font-mono block mb-1">Purity Level (γ)</span>
                <span className="text-2xl font-bold font-mono text-white">{purity.toFixed(4)}</span>
                <span className="text-[11px] text-slate-500 block mt-1">γ = Tr(ρ²) ∈ [0.18, 1.0]</span>
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
                  transition={{ duration: 0.35, ease: 'easeOut' }}
                  className="h-full rounded-full bg-gradient-to-r from-[#f43f5e] via-amber-400 to-[#10b981]"
                />
              </div>
              <div className="flex justify-between text-[10px] font-mono text-slate-500">
                <span>0.0 (Maximally Mixed I/2ⁿ)</span>
                <span>0.5</span>
                <span>1.0 (Pure State |ψ⟩⟨ψ|)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Interactive 3D Bloch Sphere */}
        <div className="lg:col-span-6 bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6 flex flex-col items-center justify-between">
          <div className="w-full flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 block">
                Interactive 3D Bloch Sphere & Purity Shell
              </span>
              <span className="text-[11px] font-mono text-slate-400">
                Drag to rotate in 3D · Vector shrinks as Tr(ρ²) decays
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => setAutoOrbit(!autoOrbit)}
                className={`px-2 py-1 rounded text-[10px] font-mono border transition-all ${
                  autoOrbit
                    ? 'bg-[#00f5ff]/15 text-[#00f5ff] border-[#00f5ff]/40'
                    : 'bg-white/5 text-slate-400 border-white/10 hover:text-white'
                }`}
              >
                {autoOrbit ? 'Orbit: ON' : 'Orbit: OFF'}
              </button>
              <button
                type="button"
                onClick={() => {
                  rotRef.current = { yaw: -0.62, pitch: 0.38 };
                }}
                className="p-1 rounded bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300"
                title="Reset 3D camera angle"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* 3D Interactive Canvas */}
          <div className="relative my-1 flex items-center justify-center select-none">
            <canvas
              ref={canvasRef}
              style={{ width: '300px', height: '300px' }}
              className="cursor-grab active:cursor-grabbing"
              onMouseDown={(e) => {
                dragRef.current = { active: true, lastX: e.clientX, lastY: e.clientY };
              }}
              onMouseMove={(e) => {
                if (!dragRef.current.active) return;
                const dx = e.clientX - dragRef.current.lastX;
                const dy = e.clientY - dragRef.current.lastY;
                dragRef.current.lastX = e.clientX;
                dragRef.current.lastY = e.clientY;
                rotRef.current.yaw += dx * 0.012;
                rotRef.current.pitch = Math.max(-1.25, Math.min(1.25, rotRef.current.pitch + dy * 0.012));
              }}
              onMouseUp={() => {
                dragRef.current.active = false;
              }}
              onMouseLeave={() => {
                dragRef.current.active = false;
              }}
            />
          </div>

          {/* Live Bloch Vector Coordinates & Shrinkage Telemetry */}
          <div className="w-full grid grid-cols-3 gap-2 pt-2 border-t border-white/10 text-center text-xs font-mono">
            <div className="bg-[#090a0f]/80 rounded-lg p-2 border border-white/5">
              <div className="text-[10px] text-slate-400 uppercase">Bloch Radius |r⃗|</div>
              <div className="text-[#00f5ff] font-bold">{blochRadius.toFixed(3)} / 1.000</div>
            </div>
            <div className="bg-[#090a0f]/80 rounded-lg p-2 border border-white/5">
              <div className="text-[10px] text-slate-400 uppercase">Angles (θ, φ)</div>
              <div className="text-white font-bold">
                {((theta * 180) / Math.PI).toFixed(0)}°, {(((phi % (2 * Math.PI)) * 180) / Math.PI).toFixed(0)}°
              </div>
            </div>
            <div className="bg-[#090a0f]/80 rounded-lg p-2 border border-white/5">
              <div className="text-[10px] text-slate-400 uppercase">Vector (rx, ry, rz)</div>
              <div className="text-[#a855f7] font-bold">
                ({rx.toFixed(2)}, {ry.toFixed(2)}, {rz.toFixed(2)})
              </div>
            </div>
          </div>
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
            {statevector ? 'Live Kraus Decoherence Stream (First 8 Basis States)' : 'Baseline Statevector Amplitudes'}
          </span>
        </div>

        {/* Amplitude Flex Bar Chart */}
        <div className="grid grid-cols-4 sm:grid-cols-8 gap-3 pt-2">
          {amplitudes.map((amp, idx) => {
            const heightPercent = Math.max(8, Math.min(100, Math.round(Math.abs(amp) * 180)));
            return (
              <div key={idx} className="flex flex-col items-center gap-2">
                <div className="w-full h-32 bg-[#090a0f] border border-white/10 rounded-lg p-1.5 flex flex-col justify-end items-center relative overflow-hidden group">
                  <span className="text-[10px] font-mono text-cyan-200 mb-1 z-10">{amp.toFixed(3)}</span>
                  <motion.div
                    animate={{ height: `${heightPercent}%` }}
                    transition={{ duration: 0.25 }}
                    className="w-full bg-gradient-to-t from-cyan-600 to-[#00f5ff] rounded shadow-[0_0_8px_rgba(0,245,255,0.3)] group-hover:brightness-125 transition-all"
                  />
                </div>
                <span className="text-[11px] font-mono text-slate-400">{basisLabels[idx] || `|${idx}⟩`}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default StageNoiseChamber;
