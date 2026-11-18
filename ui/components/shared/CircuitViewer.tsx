'use client';

import React from 'react';

export interface CircuitViewerProps {
  qubits: number;
  depth: number;
  cnotCount: number;
  encoding: 'frqi' | 'neqr';
}

export const CircuitViewer: React.FC<CircuitViewerProps> = ({
  qubits,
  depth,
  cnotCount,
  encoding,
}) => {
  if (!qubits || qubits <= 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 rounded-xl border border-white/10 bg-white/[0.02] text-slate-400 font-mono text-xs">
        Circuit will appear after compilation
      </div>
    );
  }

  // Display up to 8 qubits visually
  const displayQubits = Math.min(Math.max(1, qubits), 8);
  const wireHeight = 36;
  const topPadding = 24;
  const leftPadding = 50;
  const rightPadding = 30;
  const svgWidth = 560;
  const svgHeight = topPadding * 2 + (displayQubits - 1) * wireHeight;
  const availableWidth = svgWidth - leftPadding - rightPadding;

  // Single-qubit gate label based on encoding
  const singleGateLabel = encoding === 'neqr' ? 'X' : 'Ry';

  // Deterministic gate placement based on depth and cnotCount
  // We distribute single-qubit gates and CNOT gates across columns (depth steps)
  const effectiveDepth = Math.max(depth || 4, 4);
  const stepWidth = availableWidth / (effectiveDepth + 1);

  // Generate deterministic gate layout
  interface SingleGate {
    qubit: number;
    x: number;
    label: string;
  }
  interface CnotGate {
    ctrl: number;
    target: number;
    x: number;
  }

  const singleGates: SingleGate[] = [];
  const cnotGates: CnotGate[] = [];

  const effectiveCnot = Math.max(cnotCount || 0, 0);

  for (let d = 1; d <= effectiveDepth; d++) {
    const x = leftPadding + d * stepWidth;
    // Check if this step places a CNOT or single-qubit gates
    // Deterministic pseudo-pattern based on d, cnotCount, depth
    const isCnotStep = effectiveCnot > 0 && d % 2 === 0 && displayQubits >= 2;

    if (isCnotStep && cnotGates.length < effectiveCnot) {
      const ctrl = (d - 1) % displayQubits;
      let target = (ctrl + 1) % displayQubits;
      if (ctrl === target) target = (ctrl + 2) % displayQubits;
      cnotGates.push({ ctrl, target, x });
    } else {
      // Place single qubit gates on 1-2 wires
      const q1 = (d * 3) % displayQubits;
      singleGates.push({ qubit: q1, x, label: singleGateLabel });
      if (displayQubits > 3 && d % 2 === 1) {
        const q2 = (d * 5 + 1) % displayQubits;
        if (q2 !== q1) {
          singleGates.push({ qubit: q2, x, label: singleGateLabel });
        }
      }
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-white/10 bg-white/[0.02] p-4 backdrop-blur">
      <div className="overflow-x-auto w-full flex justify-center">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full max-w-[600px] h-auto select-none"
        >
          {/* Horizontal qubit wires and labels */}
          {Array.from({ length: displayQubits }).map((_, qIdx) => {
            const y = topPadding + qIdx * wireHeight;
            return (
              <g key={`wire-${qIdx}`}>
                {/* Qubit label */}
                <text
                  x={leftPadding - 12}
                  y={y + 4}
                  textAnchor="end"
                  fill="#94a3b8"
                  fontSize="11"
                  className="font-mono font-medium"
                >
                  q[{qIdx}]
                </text>
                {/* Horizontal wire */}
                <line
                  x1={leftPadding}
                  y1={y}
                  x2={svgWidth - rightPadding}
                  y2={y}
                  stroke="#334155"
                  strokeWidth="1.5"
                />
              </g>
            );
          })}

          {/* CNOT gates (vertical line with control dot and target target/cross) */}
          {cnotGates.map((cnot, idx) => {
            const yCtrl = topPadding + cnot.ctrl * wireHeight;
            const yTgt = topPadding + cnot.target * wireHeight;
            return (
              <g key={`cnot-${idx}`}>
                {/* Connecting line */}
                <line
                  x1={cnot.x}
                  y1={yCtrl}
                  x2={cnot.x}
                  y2={yTgt}
                  stroke="#a855f7"
                  strokeWidth="2"
                />
                {/* Control node: solid violet dot */}
                <circle cx={cnot.x} cy={yCtrl} r="4" fill="#a855f7" />
                {/* Target node: target ring + cross */}
                <circle
                  cx={cnot.x}
                  cy={yTgt}
                  r="7"
                  fill="#090a0f"
                  stroke="#a855f7"
                  strokeWidth="1.5"
                />
                <line
                  x1={cnot.x - 5}
                  y1={yTgt}
                  x2={cnot.x + 5}
                  y2={yTgt}
                  stroke="#a855f7"
                  strokeWidth="1.5"
                />
                <line
                  x1={cnot.x}
                  y1={yTgt - 5}
                  x2={cnot.x}
                  y2={yTgt + 5}
                  stroke="#a855f7"
                  strokeWidth="1.5"
                />
              </g>
            );
          })}

          {/* Single-qubit gates (colored cyan box) */}
          {singleGates.map((gate, idx) => {
            const y = topPadding + gate.qubit * wireHeight;
            const boxWidth = 22;
            const boxHeight = 20;
            return (
              <g key={`gate-${idx}`}>
                <rect
                  x={gate.x - boxWidth / 2}
                  y={y - boxHeight / 2}
                  width={boxWidth}
                  height={boxHeight}
                  rx="3"
                  fill="#090a0f"
                  stroke="#00f5ff"
                  strokeWidth="1.5"
                  className="filter drop-shadow-[0_0_4px_rgba(0,245,255,0.4)]"
                />
                <text
                  x={gate.x}
                  y={y + 3.5}
                  textAnchor="middle"
                  fill="#00f5ff"
                  fontSize="9"
                  fontWeight="bold"
                  className="font-mono"
                >
                  {gate.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Circuit Stats Footer */}
      <div className="flex items-center justify-between border-t border-white/5 pt-2 text-xs font-mono text-slate-400">
        <div>
          <span className="text-white/60">Encoding:</span>{' '}
          <span className="text-cyan-400 font-semibold">{encoding?.toUpperCase() || 'FRQI'}</span>
        </div>
        <div>
          Depth: <span className="text-white font-medium">{depth || 0}</span> | CNOT:{' '}
          <span className="text-violet-400 font-medium">{cnotCount || 0}</span> | Qubits:{' '}
          <span className="text-emerald-400 font-medium">{qubits || 0}</span>
        </div>
      </div>
    </div>
  );
};

export default CircuitViewer;
