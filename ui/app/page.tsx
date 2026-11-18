'use client';

import React from 'react';
import { Play, RotateCcw, Activity } from 'lucide-react';
import PipelineStepper from '@/components/shared/PipelineStepper';
import { useQuantumStore } from '@/lib/quantumStore';
import { useQuantumStream } from '@/lib/useQuantumStream';
import { SimulationRequest } from '@/lib/types';

import StageIngestion from '@/components/stages/StageIngestion';
import StageEncoding from '@/components/stages/StageEncoding';
import StageNoiseChamber from '@/components/stages/StageNoiseChamber';
import StageDenoiseArena from '@/components/stages/StageDenoiseArena';
import StageTomography from '@/components/stages/StageTomography';
import StageAnalytics from '@/components/stages/StageAnalytics';

const DEFAULT_SIMULATION_REQUEST: SimulationRequest = {
  resolution: 4,
  pattern: 'checkerboard',
  encoding: 'frqi',
  noise_channel: 'depolarizing',
  noise_rate: 0.01,
  shots: 10000,
  denoise_method: 'qhwt',
  threshold: 0.2,
};

export default function QuantumStudioDashboard() {
  const { activeStage, setActiveStage, isRunning, resetPipeline, events } = useQuantumStore();
  const { isConnected, error, send } = useQuantumStream();

  // Latest stage name for the live progress bar
  const lastStage = [...events].reverse().find((e) => e.event_type === 'STAGE_STARTED');
  const stageLabel =
    lastStage && lastStage.event_type === 'STAGE_STARTED'
      ? lastStage.stage_name
      : 'Initializing Quantum Register & State Synthesis...';

  const handleRunSimulation = () => {
    const { config } = useQuantumStore.getState();
    send({ ...DEFAULT_SIMULATION_REQUEST, ...config });
  };

  const renderActiveStage = () => {
    switch (activeStage) {
      case 1:
        return <StageIngestion />;
      case 2:
        return <StageEncoding />;
      case 3:
        return <StageNoiseChamber />;
      case 4:
        return <StageDenoiseArena />;
      case 5:
        return <StageTomography />;
      case 6:
        return <StageAnalytics />;
      default:
        return <StageIngestion />;
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-[#090a0f] text-[#e2e8f0]">
      {/* Top Header Bar */}
      <header className="border-b border-white/10 bg-white/[0.02] backdrop-blur-md px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-[#00f5ff] to-[#a855f7] flex items-center justify-center font-bold text-[#090a0f] text-lg shadow-[0_0_15px_rgba(0,245,255,0.4)]">
              Ψ
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                QIP Quantum Studio
              </h1>
              <p className="text-xs text-slate-400">
                Quantum Image Processing & Reconstruction Pipeline
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* WebSocket Status Indicator */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/10 text-xs">
              <span
                className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-[#10b981] shadow-[0_0_8px_#10b981]' : 'bg-[#f43f5e]'
                }`}
              />
              <span className="text-slate-300">
                {isConnected ? 'Backend Connected' : error ? 'Connection Error' : 'Connecting...'}
              </span>
            </div>

            {/* Pipeline Status Indicator */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/10 text-xs">
              <Activity
                className={`w-3.5 h-3.5 ${
                  isRunning ? 'text-[#00f5ff] animate-pulse' : 'text-slate-400'
                }`}
              />
              <span className="text-slate-300 font-mono">
                {isRunning ? 'RUNNING' : 'IDLE'}
              </span>
            </div>

            {/* Action Buttons */}
            <button
              type="button"
              onClick={resetPipeline}
              className="p-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-colors"
              title="Reset Pipeline"
            >
              <RotateCcw className="w-4 h-4" />
            </button>

            <button
              type="button"
              onClick={handleRunSimulation}
              disabled={isRunning}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#00f5ff] text-[#090a0f] font-semibold text-sm hover:brightness-110 active:brightness-95 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-[0_0_15px_rgba(0,245,255,0.3)] glow-cyan"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>{isRunning ? 'Simulating...' : 'Run Simulation'}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 flex flex-col gap-6">
        {/* Live run status */}
        {isRunning && (
          <section className="rounded-xl border border-[#00f5ff]/30 bg-[#00f5ff]/5 px-4 py-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="flex items-center gap-2 text-[#00f5ff]">
                <span className="w-2 h-2 rounded-full bg-[#00f5ff] animate-pulse" />
                Step {activeStage}/6 · {stageLabel}
              </span>
              <span className="text-slate-400">
                {Math.round((activeStage / 6) * 100)}% Complete
              </span>
            </div>
            <div className="mt-2 h-1 w-full rounded-full bg-white/10 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-[#00f5ff] to-[#a855f7] transition-all duration-700"
                style={{ width: `${(activeStage / 6) * 100}%` }}
              />
            </div>
          </section>
        )}

        {/* Pipeline Stepper */}
        <section>
          <PipelineStepper
            activeStage={activeStage}
            onStageClick={(stage) => setActiveStage(stage)}
          />
        </section>

        {/* Active Stage Container */}
        <section className="flex-1 w-full min-h-[500px]">
          {renderActiveStage()}
        </section>
      </main>
    </div>
  );
}
