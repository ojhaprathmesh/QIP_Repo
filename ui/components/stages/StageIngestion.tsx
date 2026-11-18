'use client';

import React, { useState, useMemo, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Upload, Image as ImageIcon, Sparkles, Sliders, X } from 'lucide-react';
import { useQuantumStore } from '@/lib/quantumStore';

type PatternId = 'cameraman' | 'lunar' | 'shepp_logan' | 'checkerboard' | 'gradient' | 'custom';
type InterpolationKernel = 'area' | 'bilinear' | 'nearest';

const RAW_BUFFER_SIZE = 128;
const P_CRIT = 0.008;

/** Generate high-res (128x128) source luminance buffer in [0, 1] for built-in benchmarks. */
function generateSourceBuffer(pattern: PatternId): number[][] {
  const size = RAW_BUFFER_SIZE;
  const buf: number[][] = [];
  for (let y = 0; y < size; y++) {
    const ny = y / (size - 1);
    const row: number[] = [];
    for (let x = 0; x < size; x++) {
      const nx = x / (size - 1);
      let v = 0.5;

      if (pattern === 'checkerboard') {
        const cell = Math.floor(nx * 8) + Math.floor(ny * 8);
        v = cell % 2 === 0 ? 0.92 : 0.08;
      } else if (pattern === 'gradient') {
        v = (nx + ny) / 2.0;
      } else if (pattern === 'cameraman') {
        // Canonical USC-SIPI Cameraman composition: sky gradient, distant skyline, coat silhouette, camera & tripod
        const sky = 0.82 - 0.22 * ny + 0.03 * Math.sin(nx * 8.0);
        const buildings = 0.48 + 0.1 * Math.sin(nx * 38.0);
        const ground = 0.34 + 0.06 * Math.cos(nx * 14.0 + ny * 8.0);
        v = ny < 0.62 ? sky : ny < 0.69 ? buildings : ground;

        // Head & hat silhouette
        const headDist = (nx - 0.34) ** 2 / 0.0055 + (ny - 0.23) ** 2 / 0.009;
        if (headDist < 1.0) v = 0.14;
        // Coat & torso with mid-frequency fabric texture
        if (nx >= 0.21 && nx <= 0.45 && ny >= 0.31 && ny <= 0.88 && nx - 0.21 <= (ny - 0.22) * 0.55) {
          v = 0.09 + 0.04 * Math.sin(nx * 45.0) * Math.cos(ny * 45.0);
        }
        // Extended arm holding camera
        if (nx >= 0.42 && nx <= 0.54 && ny >= 0.35 && ny <= 0.43) {
          v = 0.12;
        }
        // Camera body & bright metallic lens mount
        if (nx >= 0.52 && nx <= 0.64 && ny >= 0.30 && ny <= 0.44) {
          v = nx > 0.59 ? 0.92 : 0.22;
        }
        // Tripod legs (high-contrast geometric lines)
        if (ny >= 0.44) {
          const dt = ny - 0.44;
          const leg1 = Math.abs(nx - (0.56 - 0.24 * dt));
          const leg2 = Math.abs(nx - (0.57 + 0.04 * dt));
          const leg3 = Math.abs(nx - (0.58 + 0.28 * dt));
          if (leg1 < 0.018 || leg2 < 0.016 || leg3 < 0.018) {
            v = 0.16;
          }
        }
      } else if (pattern === 'lunar') {
        // Astronomical Lunar Crater topography with fractal terrain & shadow rims
        let base =
          0.52 +
          0.1 * Math.sin(nx * 6.0 + ny * 4.0) +
          0.05 * Math.cos(nx * 19.0 - ny * 15.0);
        const craters: [number, number, number][] = [
          [0.32, 0.36, 0.21],
          [0.71, 0.63, 0.24],
          [0.66, 0.24, 0.13],
          [0.24, 0.74, 0.14],
        ];
        for (const [cx, cy, rad] of craters) {
          const dx = nx - cx;
          const dy = ny - cy;
          const d = Math.sqrt(dx * dx + dy * dy);
          if (d < rad) {
            // Oblique solar illumination shadow inside crater bowl
            base = 0.24 + 0.32 * (d / rad) + 0.2 * (dx / rad);
          } else if (d < rad * 1.2) {
            const rimFactor = 1.0 - (d - rad) / (rad * 0.2);
            base = Math.min(0.96, base + 0.26 * rimFactor * (0.6 + 0.4 * (dx / d)));
          }
        }
        v = Math.min(1.0, Math.max(0.04, base));
      } else if (pattern === 'shepp_logan') {
        // Shepp-Logan biomedical CT phantom
        const cx = (nx - 0.5) * 2.0;
        const cy = (ny - 0.5) * 2.0;
        const outer = (cx * cx) / (0.69 * 0.69) + (cy * cy) / (0.92 * 0.92);
        const inner = (cx * cx) / (0.62 * 0.62) + ((cy + 0.02) * (cy + 0.02)) / (0.85 * 0.85);
        if (outer <= 1.0) {
          v = inner <= 1.0 ? 0.28 : 0.94;
          // Left & right ventricles
          const lv = ((cx + 0.22) * (cx + 0.22)) / (0.16 * 0.16) + (cy * cy) / (0.38 * 0.38);
          const rv = ((cx - 0.22) * (cx - 0.22)) / (0.16 * 0.16) + (cy * cy) / (0.38 * 0.38);
          if (lv <= 1.0 || rv <= 1.0) v = 0.12;
          // High-attenuation lesion ellipses
          const t1 = (cx * cx) / (0.21 * 0.21) + ((cy - 0.35) * (cy - 0.35)) / (0.25 * 0.25);
          const t2 = (cx * cx) / (0.12 * 0.12) + ((cy + 0.42) * (cy + 0.42)) / (0.12 * 0.12);
          if (t1 <= 1.0) v = 0.62;
          if (t2 <= 1.0) v = 0.78;
        } else {
          v = 0.03;
        }
      }
      row.push(Math.min(1.0, Math.max(0.0, v)));
    }
    buf.push(row);
  }
  return buf;
}

/** Preprocess a high-res source buffer into an N x N quantum register matrix. */
function preprocessBuffer(
  src: number[][],
  targetRes: number,
  kernel: InterpolationKernel,
  gamma: number,
  contrastStretch: boolean,
  bitDepth: 4 | 8,
  previewNoise: number
): number[][] {
  const srcH = src.length;
  const srcW = src[0]?.length || srcH;
  const rawGrid: number[][] = [];
  let minVal = 1.0;
  let maxVal = 0.0;

  for (let r = 0; r < targetRes; r++) {
    const row: number[] = [];
    for (let c = 0; c < targetRes; c++) {
      let val = 0.0;
      if (kernel === 'area') {
        // Anti-aliased box integration over the source region
        const y0 = Math.floor((r * srcH) / targetRes);
        const y1 = Math.max(y0 + 1, Math.floor(((r + 1) * srcH) / targetRes));
        const x0 = Math.floor((c * srcW) / targetRes);
        const x1 = Math.max(x0 + 1, Math.floor(((c + 1) * srcW) / targetRes));
        let sum = 0.0;
        let cnt = 0;
        for (let yy = y0; yy < Math.min(srcH, y1); yy++) {
          for (let xx = x0; xx < Math.min(srcW, x1); xx++) {
            sum += src[yy][xx];
            cnt++;
          }
        }
        val = cnt > 0 ? sum / cnt : 0.0;
      } else if (kernel === 'bilinear') {
        const gy = ((r + 0.5) * srcH) / targetRes - 0.5;
        const gx = ((c + 0.5) * srcW) / targetRes - 0.5;
        const y0 = Math.max(0, Math.min(srcH - 1, Math.floor(gy)));
        const y1 = Math.max(0, Math.min(srcH - 1, y0 + 1));
        const x0 = Math.max(0, Math.min(srcW - 1, Math.floor(gx)));
        const x1 = Math.max(0, Math.min(srcW - 1, x0 + 1));
        const wy = gy - Math.floor(gy);
        const wx = gx - Math.floor(gx);
        val =
          src[y0][x0] * (1 - wx) * (1 - wy) +
          src[y0][x1] * wx * (1 - wy) +
          src[y1][x0] * (1 - wx) * wy +
          src[y1][x1] * wx * wy;
      } else {
        // Nearest-neighbor point sample
        const sy = Math.min(srcH - 1, Math.floor(((r + 0.5) * srcH) / targetRes));
        const sx = Math.min(srcW - 1, Math.floor(((c + 0.5) * srcW) / targetRes));
        val = src[sy][sx];
      }

      minVal = Math.min(minVal, val);
      maxVal = Math.max(maxVal, val);
      row.push(val);
    }
    rawGrid.push(row);
  }

  const levels = (1 << bitDepth) - 1; // 255 for 8-bit, 15 for 4-bit
  const span = maxVal - minVal;

  return rawGrid.map((row, r) =>
    row.map((v, c) => {
      let norm = contrastStretch && span > 1e-4 ? (v - minVal) / span : v;
      norm = Math.pow(Math.min(1.0, Math.max(0.0, norm)), gamma);
      // Quantize to q-bit computational basis levels
      let quant = Math.round(norm * levels) / levels;
      if (previewNoise > 0) {
        const pseudo = Math.sin(r * 997 + c * 331) * previewNoise * 14.0;
        quant = Math.min(1.0, Math.max(0.0, quant + pseudo));
      }
      return Number(quant.toFixed(4));
    })
  );
}

export const StageIngestion: React.FC = () => {
  const initial = useQuantumStore.getState().config;
  const setConfig = useQuantumStore((s) => s.setConfig);

  const [resolution, setResolution] = useState<number>(initial.resolution || 16);
  const [pattern, setPattern] = useState<PatternId>((initial.pattern as PatternId) || 'cameraman');
  const [encoding, setEncoding] = useState<'frqi' | 'neqr'>(initial.encoding || 'neqr');
  const [bitDepth, setBitDepth] = useState<4 | 8>(initial.bit_depth || 8);
  const [interpolation, setInterpolation] = useState<InterpolationKernel>(initial.interpolation || 'area');
  const [gamma, setGamma] = useState<number>(initial.gamma || 1.0);
  const [contrastStretch, setContrastStretch] = useState<boolean>(initial.contrast_stretch ?? true);
  const [noiseRate, setNoiseRate] = useState<number>(initial.noise_rate ?? 0.003);

  // Uploaded custom real-world image state
  const [customSourceBuffer, setCustomSourceBuffer] = useState<number[][] | null>(null);
  const [customPreviewUrl, setCustomPreviewUrl] = useState<string | null>(null);
  const [customFileName, setCustomFileName] = useState<string | null>(initial.custom_image_name || null);
  const [customDimensions, setCustomDimensions] = useState<{ w: number; h: number } | null>(null);
  const [hoverInfo, setHoverInfo] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const previewCanvasRef = useRef<HTMLCanvasElement | null>(null);

  // Build high-res source buffer from uploaded image or selected preset
  const activeSourceBuffer = useMemo(() => {
    if (pattern === 'custom' && customSourceBuffer) {
      return customSourceBuffer;
    }
    return generateSourceBuffer(pattern === 'custom' ? 'cameraman' : pattern);
  }, [pattern, customSourceBuffer]);

  // Preprocess into target N x N quantum register matrix
  const processedMatrix = useMemo(
    () =>
      preprocessBuffer(
        activeSourceBuffer,
        resolution,
        interpolation,
        gamma,
        contrastStretch,
        bitDepth,
        noiseRate
      ),
    [activeSourceBuffer, resolution, interpolation, gamma, contrastStretch, bitDepth, noiseRate]
  );

  // Also compute clean (zero-noise) preprocessed matrix to send to backend simulator
  const cleanPreprocessedMatrix = useMemo(
    () =>
      preprocessBuffer(
        activeSourceBuffer,
        resolution,
        interpolation,
        gamma,
        contrastStretch,
        bitDepth,
        0
      ),
    [activeSourceBuffer, resolution, interpolation, gamma, contrastStretch, bitDepth]
  );

  // Sync user's ingestion & preprocessing configuration to global store
  useEffect(() => {
    setConfig({
      resolution,
      pattern,
      encoding,
      noise_rate: noiseRate,
      bit_depth: bitDepth,
      interpolation,
      gamma,
      contrast_stretch: contrastStretch,
      custom_pixels: cleanPreprocessedMatrix,
      custom_image_name: customFileName,
    });
  }, [
    resolution,
    pattern,
    encoding,
    noiseRate,
    bitDepth,
    interpolation,
    gamma,
    contrastStretch,
    cleanPreprocessedMatrix,
    customFileName,
    setConfig,
  ]);

  // Decode uploaded real-world image via offscreen HTML5 Canvas -> normalized grayscale matrix
  const handleImageFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target?.result as string;
      if (!dataUrl) return;
      const img = new window.Image();
      img.onload = () => {
        setCustomDimensions({ w: img.naturalWidth, h: img.naturalHeight });
        const canvas = document.createElement('canvas');
        canvas.width = RAW_BUFFER_SIZE;
        canvas.height = RAW_BUFFER_SIZE;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Center-crop square from uploaded image for distortion-free 2^n x 2^n register mapping
        const side = Math.min(img.naturalWidth, img.naturalHeight);
        const sx = (img.naturalWidth - side) / 2;
        const sy = (img.naturalHeight - side) / 2;
        ctx.drawImage(img, sx, sy, side, side, 0, 0, RAW_BUFFER_SIZE, RAW_BUFFER_SIZE);

        const imgData = ctx.getImageData(0, 0, RAW_BUFFER_SIZE, RAW_BUFFER_SIZE).data;
        const buf: number[][] = [];
        for (let y = 0; y < RAW_BUFFER_SIZE; y++) {
          const row: number[] = [];
          for (let x = 0; x < RAW_BUFFER_SIZE; x++) {
            const idx = (y * RAW_BUFFER_SIZE + x) * 4;
            // ITU-R BT.709 perceived luminance conversion
            const lum = (0.2126 * imgData[idx] + 0.7152 * imgData[idx + 1] + 0.0722 * imgData[idx + 2]) / 255.0;
            row.push(lum);
          }
          buf.push(row);
        }
        setCustomSourceBuffer(buf);
        setCustomPreviewUrl(dataUrl);
        setCustomFileName(file.name);
        setPattern('custom');
      };
      img.src = dataUrl;
    };
    reader.readAsDataURL(file);
  };

  // Resolution n calculation: N = 2^n -> n = log2(resolution)
  const n = useMemo(() => Math.round(Math.log2(resolution)), [resolution]);
  const frqiQubits = 2 * n + 1;
  const neqrQubits = 2 * n + bitDepth;
  const isSubCritical = noiseRate < P_CRIT;

  // Render up to 32x32 in the interactive cell grid, or crisp HTML5 canvas for 64x64 / 128x128
  const displayMatrix = processedMatrix;
  const displayRes = displayMatrix.length;

  useEffect(() => {
    if (displayRes <= 32 || !previewCanvasRef.current) return;
    const canvas = previewCanvasRef.current;
    canvas.width = displayRes;
    canvas.height = displayRes;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const imgData = ctx.createImageData(displayRes, displayRes);
    for (let r = 0; r < displayRes; r++) {
      for (let c = 0; c < displayRes; c++) {
        const byteVal = Math.round((displayMatrix[r]?.[c] ?? 0) * 255);
        const idx = (r * displayRes + c) * 4;
        imgData.data[idx] = byteVal;
        imgData.data[idx + 1] = byteVal;
        imgData.data[idx + 2] = byteVal;
        imgData.data[idx + 3] = 255;
      }
    }
    ctx.putImageData(imgData, 0, 0);
  }, [displayMatrix, displayRes]);

  return (
    <div className="space-y-6">
      {/* Top Banner / Stage Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/10">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[#00f5ff]">Stage 01</span>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            Real-World Image Ingestion & Quantum Preprocessing
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Upload real-world photographs or select standard corpus benchmarks, configure downsampling & quantization, and map to qubits.
          </p>
        </div>

        {/* Live Qubit Requirements Display */}
        <div className="flex items-center gap-3 bg-[#090a0f] border border-[#00f5ff]/30 px-4 py-2.5 rounded-lg shadow-[0_0_15px_rgba(0,245,255,0.1)]">
          <div className="text-xs font-mono text-slate-300">
            <span className="text-slate-400">Scale:</span>{' '}
            <span className="text-white font-bold">
              {resolution}×{resolution}
            </span>{' '}
            (n={n})
          </div>
          <div className="h-4 w-[1px] bg-white/20" />
          <div className="text-xs font-mono">
            <span className="text-[#00f5ff] font-semibold">FRQI:</span> 2n+1 ={' '}
            <span className="text-white font-bold">{frqiQubits}</span> qubits
          </div>
          <div className="h-4 w-[1px] bg-white/20" />
          <div className="text-xs font-mono">
            <span className="text-[#a855f7] font-semibold">NEQR:</span> 2n+{bitDepth} ={' '}
            <span className="text-white font-bold">{neqrQubits}</span> qubits
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Real-World Image Loader & Preprocessing Controls */}
        <div className="lg:col-span-6 space-y-5 bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6">
          {/* 1. Real-World Upload Zone */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[#00f5ff] flex items-center gap-2">
                <Upload className="w-3.5 h-3.5" />
                Real-World Image Upload & Benchmark Corpus
              </h3>
              {customFileName && (
                <button
                  type="button"
                  onClick={() => {
                    setCustomSourceBuffer(null);
                    setCustomPreviewUrl(null);
                    setCustomFileName(null);
                    setCustomDimensions(null);
                    setPattern('cameraman');
                  }}
                  className="text-[11px] font-mono text-rose-400 hover:text-rose-300 flex items-center gap-1"
                >
                  <X className="w-3 h-3" /> Clear Upload
                </button>
              )}
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleImageFile(file);
              }}
            />

            <div
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const file = e.dataTransfer.files?.[0];
                if (file) handleImageFile(file);
              }}
              className={`cursor-pointer rounded-xl border border-dashed p-3.5 transition-all flex items-center justify-between gap-3 ${
                pattern === 'custom'
                  ? 'border-[#00f5ff] bg-[#00f5ff]/10 shadow-[0_0_15px_rgba(0,245,255,0.15)]'
                  : 'border-white/20 bg-[#090a0f]/60 hover:border-[#00f5ff]/50 hover:bg-white/[0.04]'
              }`}
            >
              <div className="flex items-center gap-3 min-w-0">
                {customPreviewUrl ? (
                  <img
                    src={customPreviewUrl}
                    alt="Uploaded source"
                    className="w-11 h-11 rounded-lg object-cover border border-[#00f5ff]/40 shrink-0"
                  />
                ) : (
                  <div className="w-10 h-10 rounded-lg bg-[#00f5ff]/10 border border-[#00f5ff]/30 flex items-center justify-center text-[#00f5ff] shrink-0">
                    <ImageIcon className="w-5 h-5" />
                  </div>
                )}
                <div className="min-w-0">
                  <div className="text-xs font-semibold text-white truncate">
                    {customFileName ? `Uploaded: ${customFileName}` : 'Upload Any Real-World Image (Drop or Click)'}
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono truncate">
                    {customDimensions
                      ? `Source ${customDimensions.w}×${customDimensions.h}px → ITU-R BT.709 Luminance → ${resolution}×${resolution} Register`
                      : 'PNG, JPG, WebP · Auto center-crop, BT.709 grayscale & anti-aliased downsampling'}
                  </div>
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-md text-[11px] font-mono font-semibold bg-[#00f5ff]/15 text-[#00f5ff] border border-[#00f5ff]/30 shrink-0">
                Browse...
              </span>
            </div>

            {/* Built-in Real-World Paper Benchmarks & Synthetic Patterns */}
            <div className="grid grid-cols-5 gap-1.5 pt-1">
              {(
                [
                  { id: 'cameraman', label: 'Cameraman', tag: 'USC-SIPI' },
                  { id: 'lunar', label: 'Lunar Crater', tag: 'NASA Topo' },
                  { id: 'shepp_logan', label: 'CT Phantom', tag: 'Clinical' },
                  { id: 'checkerboard', label: 'Checker', tag: 'Synthetic' },
                  { id: 'gradient', label: 'Gradient', tag: 'Synthetic' },
                ] as const
              ).map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setPattern(item.id)}
                  className={`py-1.5 px-2 rounded-lg text-left transition-all border ${
                    pattern === item.id
                      ? 'bg-[#a855f7]/20 text-white border-[#a855f7] shadow-[0_0_10px_rgba(168,85,247,0.25)]'
                      : 'bg-white/5 text-slate-400 border-white/10 hover:border-white/25 hover:text-white'
                  }`}
                >
                  <div className="text-[11px] font-semibold truncate">{item.label}</div>
                  <div className="text-[9px] font-mono text-slate-400 truncate">{item.tag}</div>
                </button>
              ))}
            </div>
          </div>

          {/* 2. Resolution & Encoding Scheme */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-3 border-t border-white/10">
            <div>
              <label className="text-xs text-slate-400 font-medium block mb-1.5">Register Resolution (N × N)</label>
              <div className="grid grid-cols-3 sm:grid-cols-6 gap-1.5">
                {[4, 8, 16, 32, 64, 128].map((res) => (
                  <button
                    key={res}
                    type="button"
                    onClick={() => setResolution(res)}
                    className={`py-1.5 px-1.5 rounded-lg text-[11px] font-mono font-medium transition-all border ${
                      resolution === res
                        ? 'bg-[#00f5ff]/20 text-[#00f5ff] border-[#00f5ff] shadow-[0_0_10px_rgba(0,245,255,0.2)]'
                        : 'bg-white/5 text-slate-400 border-white/10 hover:border-white/25 hover:text-white'
                    }`}
                  >
                    {res}×{res}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-xs text-slate-400 font-medium block mb-1.5">Quantum State Encoding</label>
              <div className="grid grid-cols-2 gap-1.5">
                {(
                  [
                    { id: 'frqi', label: 'FRQI (2n+1)', desc: 'Amplitude' },
                    { id: 'neqr', label: `NEQR (2n+${bitDepth})`, desc: 'Basis State' },
                  ] as const
                ).map((enc) => (
                  <button
                    key={enc.id}
                    type="button"
                    onClick={() => setEncoding(enc.id)}
                    className={`py-1.5 px-2.5 rounded-lg text-xs font-mono font-medium transition-all border ${
                      encoding === enc.id
                        ? 'bg-[#00f5ff]/20 text-[#00f5ff] border-[#00f5ff]'
                        : 'bg-white/5 text-slate-400 border-white/10 hover:text-white'
                    }`}
                  >
                    {enc.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 3. Preprocessing Pipeline Parameters: Interpolation, Bit-Depth, Gamma & Contrast */}
          <div className="pt-3 border-t border-white/10 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5 text-[#a855f7]" />
                Preprocessing Pipeline Parameters
              </span>
              <button
                type="button"
                onClick={() => setContrastStretch(!contrastStretch)}
                className={`px-2 py-0.5 rounded text-[10px] font-mono border transition-all ${
                  contrastStretch
                    ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40'
                    : 'bg-white/5 text-slate-400 border-white/10'
                }`}
              >
                Auto Min-Max Stretch: {contrastStretch ? 'ON' : 'OFF'}
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* Downsampling Kernel */}
              <div>
                <label className="text-[11px] text-slate-400 font-mono block mb-1">Downsampling Kernel</label>
                <div className="grid grid-cols-3 gap-1">
                  {(
                    [
                      { id: 'area', label: 'Area AA' },
                      { id: 'bilinear', label: 'Bilinear' },
                      { id: 'nearest', label: 'Nearest' },
                    ] as const
                  ).map((k) => (
                    <button
                      key={k.id}
                      type="button"
                      onClick={() => setInterpolation(k.id)}
                      className={`py-1 px-1.5 rounded text-[11px] font-mono border transition-all ${
                        interpolation === k.id
                          ? 'bg-[#a855f7]/20 text-[#a855f7] border-[#a855f7]'
                          : 'bg-white/5 text-slate-400 border-white/10 hover:text-white'
                      }`}
                    >
                      {k.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Color Bit-Depth Quantization (q) */}
              <div>
                <label className="text-[11px] text-slate-400 font-mono block mb-1">Color Quantization (q bits)</label>
                <div className="grid grid-cols-2 gap-1">
                  {(
                    [
                      { q: 8, label: '8-bit (256 lvl)' },
                      { q: 4, label: '4-bit (16 lvl)' },
                    ] as const
                  ).map((b) => (
                    <button
                      key={b.q}
                      type="button"
                      onClick={() => setBitDepth(b.q)}
                      className={`py-1 px-2 rounded text-[11px] font-mono border transition-all ${
                        bitDepth === b.q
                          ? 'bg-[#a855f7]/20 text-[#a855f7] border-[#a855f7]'
                          : 'bg-white/5 text-slate-400 border-white/10 hover:text-white'
                      }`}
                    >
                      {b.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Radiometric Gamma Correction Slider */}
            <div className="space-y-1">
              <div className="flex justify-between text-[11px] font-mono">
                <span className="text-slate-400">Radiometric Gamma Correction (γ):</span>
                <span className="text-[#a855f7] font-semibold">γ = {gamma.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.50"
                max="2.00"
                step="0.05"
                value={gamma}
                onChange={(e) => setGamma(parseFloat(e.target.value))}
                className="w-full accent-[#a855f7] bg-white/10 h-1.5 rounded-lg appearance-none cursor-pointer"
              />
            </div>
          </div>

          {/* 4. Physical NISQ Noise Rate p & Critical Horizon Selector */}
          <div className="pt-3 border-t border-white/10 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[#00f5ff]" />
                Physical Gate Error Rate (p) vs. p_crit = 0.008
              </span>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold border ${
                  isSubCritical
                    ? 'bg-[#00f5ff]/15 text-[#00f5ff] border-[#00f5ff]/40'
                    : 'bg-[#f43f5e]/15 text-[#f43f5e] border-[#f43f5e]/40'
                }`}
              >
                {isSubCritical ? 'QUANTUM ADVANTAGE (p < p_crit)' : 'CLASSICAL BM3D PREFERRED (p ≥ p_crit)'}
              </span>
            </div>

            {/* One-click regime presets */}
            <div className="grid grid-cols-3 gap-1.5">
              <button
                type="button"
                onClick={() => setNoiseRate(0.003)}
                className={`py-1.5 px-2 rounded-lg text-[11px] font-mono border transition-all ${
                  noiseRate < 0.006
                    ? 'bg-[#00f5ff]/20 text-[#00f5ff] border-[#00f5ff]'
                    : 'bg-white/5 text-slate-400 border-white/10 hover:text-white'
                }`}
              >
                Low NISQ (p=0.003)
              </button>
              <button
                type="button"
                onClick={() => setNoiseRate(0.0075)}
                className={`py-1.5 px-2 rounded-lg text-[11px] font-mono border transition-all ${
                  noiseRate >= 0.006 && noiseRate < 0.0095
                    ? 'bg-amber-500/20 text-amber-300 border-amber-400'
                    : 'bg-white/5 text-slate-400 border-white/10 hover:text-white'
                }`}
              >
                Near p_crit (p=0.0075)
              </button>
              <button
                type="button"
                onClick={() => setNoiseRate(0.016)}
                className={`py-1.5 px-2 rounded-lg text-[11px] font-mono border transition-all ${
                  noiseRate >= 0.0095
                    ? 'bg-[#f43f5e]/20 text-[#f43f5e] border-[#f43f5e]'
                    : 'bg-white/5 text-slate-400 border-white/10 hover:text-white'
                }`}
              >
                High Noise (p=0.016)
              </button>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-[11px] font-mono">
                <span className="text-slate-400">Depolarizing / Kraus Gate Error Rate p:</span>
                <span className={isSubCritical ? 'text-[#00f5ff] font-bold' : 'text-[#f43f5e] font-bold'}>
                  p = {noiseRate.toFixed(4)}
                </span>
              </div>
              <input
                type="range"
                min="0.0005"
                max="0.0250"
                step="0.0005"
                value={noiseRate}
                onChange={(e) => setNoiseRate(parseFloat(e.target.value))}
                className={`w-full bg-white/10 h-1.5 rounded-lg appearance-none cursor-pointer ${
                  isSubCritical ? 'accent-[#00f5ff]' : 'accent-[#f43f5e]'
                }`}
              />
            </div>
          </div>
        </div>

        {/* Right: Preprocessed Quantum Register Matrix Visualization */}
        <div className="lg:col-span-6 bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6 flex flex-col items-center justify-between">
          <div className="w-full flex items-center justify-between mb-3">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 block">
                Preprocessed Quantum Register Buffer ({displayRes}×{displayRes})
              </span>
              <span className="text-[11px] font-mono text-slate-400">
                Kernel: {interpolation.toUpperCase()} · {bitDepth}-bit ({1 << bitDepth} levels) · γ={gamma.toFixed(2)}
              </span>
            </div>
            <span className="px-2.5 py-1 rounded-md text-xs font-mono bg-[#090a0f] border border-white/10 text-slate-300">
              {pattern === 'custom' && customFileName ? customFileName : pattern.replace('_', ' ').toUpperCase()}
            </span>
          </div>

          <div className="relative p-3 rounded-xl bg-[#090a0f] border border-white/10 shadow-[0_0_30px_rgba(0,0,0,0.5)] my-2">
            {displayRes <= 32 ? (
              <motion.div
                key={`${pattern}-${resolution}-${interpolation}-${bitDepth}-${gamma}-${contrastStretch}-${customFileName}`}
                initial={{ opacity: 0.7, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.2 }}
                className="grid gap-[1.5px]"
                style={{
                  gridTemplateColumns: `repeat(${displayRes}, minmax(0, 1fr))`,
                  width: '320px',
                  height: '320px',
                }}
              >
                {displayMatrix.map((row, rIdx) =>
                  row.map((val, cIdx) => {
                    const byteVal = Math.round(val * 255);
                    return (
                      <div
                        key={`${rIdx}-${cIdx}`}
                        className="relative group rounded-[1px]"
                        style={{
                          backgroundColor: `rgb(${byteVal}, ${byteVal}, ${byteVal})`,
                        }}
                        title={`(${rIdx}, ${cIdx}) → g=${val.toFixed(3)} | level=${Math.round(
                          val * ((1 << bitDepth) - 1)
                        )}/${(1 << bitDepth) - 1}`}
                      >
                        <div className="opacity-0 group-hover:opacity-100 absolute inset-0 bg-[#00f5ff]/40 pointer-events-none" />
                      </div>
                    );
                  })
                )}
              </motion.div>
            ) : (
              <div className="relative" style={{ width: '320px', height: '320px' }}>
                <canvas
                  ref={previewCanvasRef}
                  onMouseMove={(e) => {
                    const rect = e.currentTarget.getBoundingClientRect();
                    const cIdx = Math.min(displayRes - 1, Math.max(0, Math.floor(((e.clientX - rect.left) / rect.width) * displayRes)));
                    const rIdx = Math.min(displayRes - 1, Math.max(0, Math.floor(((e.clientY - rect.top) / rect.height) * displayRes)));
                    const val = displayMatrix[rIdx]?.[cIdx] ?? 0;
                    const maxLvl = (1 << bitDepth) - 1;
                    setHoverInfo(`(${rIdx}, ${cIdx}) → g=${val.toFixed(3)} | level=${Math.round(val * maxLvl)}/${maxLvl}`);
                  }}
                  onMouseLeave={() => setHoverInfo(null)}
                  className="w-full h-full rounded cursor-crosshair"
                  style={{ imageRendering: 'pixelated' }}
                />
                {hoverInfo && (
                  <div className="absolute bottom-2 left-2 right-2 px-2.5 py-1 rounded bg-[#090a0f]/90 border border-[#00f5ff]/40 text-[11px] font-mono text-[#00f5ff] text-center pointer-events-none">
                    {hoverInfo}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Bottom Summary Bar */}
          <div className="w-full mt-3 pt-3 border-t border-white/10 grid grid-cols-3 gap-2 text-center text-xs font-mono">
            <div className="bg-[#090a0f]/70 rounded-lg p-2 border border-white/5">
              <div className="text-[10px] text-slate-400 uppercase">Hilbert Dimension</div>
              <div className="text-white font-bold">
                2^{encoding === 'frqi' ? frqiQubits : neqrQubits} states
              </div>
            </div>
            <div className="bg-[#090a0f]/70 rounded-lg p-2 border border-white/5">
              <div className="text-[10px] text-slate-400 uppercase">Bit-Flip Variance</div>
              <div className="text-[#a855f7] font-bold">
                {bitDepth === 8 ? '21,845× (q=8)' : '85× (q=4 UEP)'}
              </div>
            </div>
            <div className="bg-[#090a0f]/70 rounded-lg p-2 border border-white/5">
              <div className="text-[10px] text-slate-400 uppercase">Expected Regime</div>
              <div className={isSubCritical ? 'text-[#00f5ff] font-bold' : 'text-[#f43f5e] font-bold'}>
                {isSubCritical ? 'Quantum QHWT' : 'Classical BM3D'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StageIngestion;
