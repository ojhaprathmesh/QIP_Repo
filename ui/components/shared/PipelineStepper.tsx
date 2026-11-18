'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Check } from 'lucide-react';

export interface PipelineStepperProps {
  activeStage: number;
  onStageClick: (stageNumber: number) => void;
}

const STAGE_LABELS = [
  'Ingestion',
  'Encoding',
  'Noise Chamber',
  'Denoising',
  'Tomography',
  'Analytics',
];

export const PipelineStepper: React.FC<PipelineStepperProps> = ({
  activeStage,
  onStageClick,
}) => {
  return (
    <nav
      aria-label="Pipeline Stages"
      className="w-full overflow-x-auto py-3 px-2"
    >
      <div className="flex items-center justify-between min-w-[640px] gap-2 p-2 rounded-2xl bg-white/[0.02] backdrop-blur-md border border-white/10">
        {STAGE_LABELS.map((label, index) => {
          const stageNumber = index + 1;
          const isActive = stageNumber === activeStage;
          const isCompleted = stageNumber < activeStage;
          const isUpcoming = stageNumber > activeStage;

          return (
            <button
              key={label}
              type="button"
              onClick={() => onStageClick(stageNumber)}
              className="relative flex-1 group flex flex-col items-center py-2 px-3 rounded-xl transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00f5ff]"
            >
              {isActive && (
                <motion.div
                  layoutId="active-pipeline-indicator"
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
                  {label}
                </span>
              </div>

              <div className="relative z-10 w-full flex items-center gap-1 px-1">
                <div
                  className={`h-1 w-full rounded-full transition-all ${
                    isActive
                      ? 'bg-[#00f5ff]'
                      : isCompleted
                      ? 'bg-[#10b981]/50'
                      : 'bg-white/10'
                  }`}
                />
              </div>
            </button>
          );
        })}
      </div>
    </nav>
  );
};

export default PipelineStepper;
