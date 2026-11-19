'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Check } from 'lucide-react';

export interface PipelineStepperProps {
  activeStage: number;
  onStageClick: (stageNumber: number) => void;
  orientation?: 'horizontal' | 'vertical';
}

const STAGES = [
  { id: 1, label: 'Ingestion', desc: 'Matrix Preprocessing' },
  { id: 2, label: 'Encoding', desc: 'Circuit Synthesis' },
  { id: 3, label: 'Noise Chamber', desc: 'Kraus Decoherence' },
  { id: 4, label: 'Denoising', desc: 'Quantum vs Classical' },
  { id: 5, label: 'Tomography', desc: 'Shot Measurement' },
  { id: 6, label: 'Analytics', desc: 'Phase Boundary (p_crit)' },
];

export const PipelineStepper: React.FC<PipelineStepperProps> = ({
  activeStage,
  onStageClick,
  orientation = 'vertical',
}) => {
  if (orientation === 'horizontal') {
    return (
      <nav aria-label="Pipeline Stages" className="w-full overflow-x-auto py-3 px-2">
        <div className="flex items-center justify-between min-w-[640px] gap-2 p-2 rounded-2xl bg-white/[0.02] backdrop-blur-md border border-white/10">
          {STAGES.map((stage) => {
            const stageNumber = stage.id;
            const isActive = stageNumber === activeStage;
            const isCompleted = stageNumber < activeStage;

            return (
              <button
                key={stage.id}
                type="button"
                onClick={() => onStageClick(stageNumber)}
                className="relative flex-1 group flex flex-col items-center py-2 px-3 rounded-xl transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00f5ff]"
              >
                {isActive && (
                  <motion.div
                    layoutId="active-pipeline-indicator-h"
                    className="absolute inset-0 rounded-xl bg-gradient-to-r from-[#00f5ff]/15 via-[#00f5ff]/25 to-[#a855f7]/15 border border-[#00f5ff]/60 glow-cyan"
                    transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                  />
                )}

                <div className="relative z-10 flex items-center gap-2 mb-1">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold mono transition-all ${
                      isActive
                        ? 'bg-[#00f5ff] text-[#090a0f] shadow-[0_0_10px_#00f5ff]'
                        : isCompleted
                        ? 'bg-[#10b981]/20 text-[#10b981] border border-[#10b981]/40'
                        : 'bg-white/5 text-slate-500 border border-white/10'
                    }`}
                  >
                    {isCompleted ? <Check className="w-3.5 h-3.5 stroke-[2.5]" /> : stageNumber}
                  </div>
                  <span
                    className={`text-xs font-medium tracking-wide transition-colors ${
                      isActive
                        ? 'text-[#00f5ff] font-semibold'
                        : isCompleted
                        ? 'text-[#10b981]/90'
                        : 'text-slate-400 group-hover:text-slate-200'
                    }`}
                  >
                    {stage.label}
                  </span>
                </div>

                <div className="relative z-10 w-full flex items-center gap-1 px-1">
                  <div
                    className={`h-1 w-full rounded-full transition-all ${
                      isActive ? 'bg-[#00f5ff]' : isCompleted ? 'bg-[#10b981]/50' : 'bg-white/10'
                    }`}
                  />
                </div>
              </button>
            );
          })}
        </div>
      </nav>
    );
  }

  // Vertical Orientation (Pinned to the right side of the page, extends 100% height)
  return (
    <nav aria-label="Pipeline Stages" className="w-full h-full flex flex-col">
      <div className="flex flex-col h-full gap-2 p-3.5 rounded-2xl bg-white/[0.02] backdrop-blur-md border border-white/10 shadow-[0_4px_24px_rgba(0,0,0,0.4)]">
        <div className="px-3 py-2 flex items-center justify-between border-b border-white/5 mb-1 shrink-0">
          <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400">
            Pipeline Stages
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#00f5ff]/10 text-[#00f5ff] border border-[#00f5ff]/20">
            Stage {activeStage} of 6
          </span>
        </div>

        <div className="flex-1 min-h-0 flex flex-col justify-between py-1 relative">
          {STAGES.map((stage, idx) => {
            const stageNumber = stage.id;
            const isActive = stageNumber === activeStage;
            const isCompleted = stageNumber < activeStage;
            const isLast = idx === STAGES.length - 1;

            return (
              <div key={stage.id} className="relative flex-1 flex flex-col justify-center">
                {/* Connecting vertical line to next stage */}
                {!isLast && (
                  <div
                    className={`absolute left-[23px] top-1/2 h-full w-[2px] transition-colors z-0 ${
                      isCompleted ? 'bg-[#10b981]/50 shadow-[0_0_6px_rgba(16,185,129,0.3)]' : 'bg-white/10'
                    }`}
                  />
                )}

                <button
                  type="button"
                  onClick={() => onStageClick(stageNumber)}
                  className={`relative z-10 w-full group flex items-center gap-3 p-2.5 rounded-xl transition-all text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00f5ff] ${
                    isActive
                      ? 'bg-gradient-to-r from-[#00f5ff]/15 via-[#00f5ff]/20 to-[#a855f7]/10 border border-[#00f5ff]/50 shadow-[0_0_15px_rgba(0,245,255,0.15)]'
                      : 'hover:bg-white/[0.04] border border-transparent'
                  }`}
                >
                  {/* Step circle / indicator */}
                  <div
                    className={`w-7 h-7 rounded-full shrink-0 flex items-center justify-center text-xs font-semibold font-mono transition-all z-10 ${
                      isActive
                        ? 'bg-[#00f5ff] text-[#090a0f] shadow-[0_0_12px_#00f5ff]'
                        : isCompleted
                        ? 'bg-[#090a0f] text-[#10b981] border border-[#10b981]/60 shadow-[0_0_8px_rgba(16,185,129,0.2)]'
                        : 'bg-[#090a0f] text-slate-500 border border-white/10 group-hover:border-white/20'
                    }`}
                  >
                    {isCompleted ? <Check className="w-3.5 h-3.5 stroke-[2.5]" /> : stageNumber}
                  </div>

                  {/* Stage Label & Subtext */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span
                        className={`text-xs font-medium tracking-wide truncate transition-colors ${
                          isActive
                            ? 'text-[#00f5ff] font-semibold'
                            : isCompleted
                            ? 'text-slate-200'
                            : 'text-slate-400 group-hover:text-slate-300'
                        }`}
                      >
                        {stage.label}
                      </span>
                      {isActive && (
                        <span className="w-1.5 h-1.5 rounded-full bg-[#00f5ff] animate-ping shrink-0 ml-1.5" />
                      )}
                    </div>
                    <p className="text-[10px] text-slate-500 font-mono truncate mt-0.5">
                      {stage.desc}
                    </p>
                  </div>
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </nav>
  );
};

export default PipelineStepper;
