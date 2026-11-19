'use client';

import React, { useEffect, useState } from 'react';
import { Play, RotateCcw, Activity, ChevronRight, Cpu } from 'lucide-react';
import PipelineStepper from '@/components/shared/PipelineStepper';
import { useQuantumStore } from '@/lib/quantumStore';
import { useQuantumStream, getDefaultHealthUrl } from '@/lib/useQuantumStream';
import { SimulationRequest } from '@/lib/types';

import StageIngestion from '@/components/stages/StageIngestion';
import StageEncoding from '@/components/stages/StageEncoding';
import StageNoiseChamber from '@/components/stages/StageNoiseChamber';
import StageDenoiseArena from '@/components/stages/StageDenoiseArena';
import StageTomography from '@/components/stages/StageTomography';
import StageAnalytics from '@/components/stages/StageAnalytics';

const STAGE_TITLES: Record<number, string> = {
  1: 'Ingestion',
  2: 'Encoding',
  3: 'Noise Chamber',
  4: 'Denoising',
  5: 'Tomography',
  6: 'Analytics',
};

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
  const {
    activeStage,
    setActiveStage,
    isRunning,
    resetPipeline,
    events,
    stepMode,
    awaitingNextStep,
  } = useQuantumStore();
  const { isConnected, error, send, advanceStep, changeStepMode } = useQuantumStream();
  const [backendReachable, setBackendReachable] = useState<boolean>(true);

  useEffect(() => {
    let active = true;
    const probeBackend = async () => {
      try {
        const res = await fetch(getDefaultHealthUrl(), { cache: 'no-store' });
        if (active) setBackendReachable(res.ok);
      } catch {
        if (active) setBackendReachable(false);
      }
    };
    probeBackend();
    const interval = setInterval(probeBackend, 6000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  const isQiskitSimulator = isConnected && !error && backendReachable;

  // Latest stage name for the live progress bar
  const lastStage = [...events].reverse().find((e) => e.event_type === 'STAGE_STARTED');
  const stageLabel =
    lastStage && lastStage.event_type === 'STAGE_STARTED'
      ? lastStage.stage_name
      : 'Initializing Quantum Register & State Synthesis...';

  const handleRunSimulation = () => {
    const { config, stepMode: currentMode } = useQuantumStore.getState();
    send({ ...DEFAULT_SIMULATION_REQUEST, ...config, step_mode: currentMode });
  };

  // Allow advancing in Manual Step mode with Right Arrow or Space
  useEffect(() => {
    if (!isRunning || !awaitingNextStep) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === ' ') {
        const tag = (e.target as HTMLElement)?.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA') return;
        e.preventDefault();
        advanceStep();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isRunning, awaitingNextStep, advanceStep]);

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

            {/* Engine Indicator Badge */}
            <div
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-mono ${
                isQiskitSimulator
                  ? 'bg-[#00f5ff]/10 border-[#00f5ff]/30 text-[#00f5ff]'
                  : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
              }`}
              title={
                isQiskitSimulator
                  ? 'Connected to FastAPI Qiskit simulation engine'
                  : 'Running in-browser fallback simulation engine'
              }
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>{isQiskitSimulator ? 'Qiskit Simulator' : 'Client Fallback'}</span>
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

            {/* Auto Flow vs Manual Step Mode Selector */}
            <div className="flex items-center rounded-lg bg-white/[0.04] border border-white/10 p-0.5 text-xs font-mono">
              <button
                type="button"
                onClick={() => changeStepMode('auto')}
                className={`px-2.5 py-1 rounded-md transition-all ${
                  stepMode === 'auto'
                    ? 'bg-[#00f5ff]/20 text-[#00f5ff] border border-[#00f5ff]/40 font-semibold'
                    : 'text-slate-400 hover:text-white'
                }`}
                title="Automatically advance across all 6 stages"
              >
                Auto Flow
              </button>
              <button
                type="button"
                onClick={() => changeStepMode('manual')}
                className={`px-2.5 py-1 rounded-md transition-all ${
                  stepMode === 'manual'
                    ? 'bg-[#a855f7]/25 text-[#c084fc] border border-[#a855f7]/50 font-semibold'
                    : 'text-slate-400 hover:text-white'
                }`}
                title="Pause at the end of each stage until you click Next Stage"
              >
                Manual Step
              </button>
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

            {isRunning && awaitingNextStep ? (
              <button
                type="button"
                onClick={advanceStep}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-[#a855f7] to-[#00f5ff] text-[#090a0f] font-bold text-sm hover:brightness-110 active:brightness-95 transition-all shadow-[0_0_20px_rgba(168,85,247,0.45)] animate-pulse"
              >
                <span>Next: {STAGE_TITLES[activeStage + 1] || 'Finish'}</span>
                <ChevronRight className="w-4 h-4 stroke-[2.5]" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleRunSimulation}
                disabled={isRunning}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#00f5ff] text-[#090a0f] font-semibold text-sm hover:brightness-110 active:brightness-95 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-[0_0_15px_rgba(0,245,255,0.3)] glow-cyan"
              >
                <Play className="w-4 h-4 fill-current" />
                <span>{isRunning ? 'Simulating...' : 'Run Simulation'}</span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 flex flex-col gap-6">
        {/* Live run status */}
        {isRunning && (
          <section
            className={`rounded-xl border px-4 py-3 transition-colors ${
              awaitingNextStep
                ? 'border-[#a855f7]/50 bg-[#a855f7]/10'
                : 'border-[#00f5ff]/30 bg-[#00f5ff]/5'
            }`}
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono">
              <span className="flex items-center gap-2 text-[#00f5ff]">
                <span
                  className={`w-2 h-2 rounded-full ${
                    awaitingNextStep ? 'bg-[#a855f7]' : 'bg-[#00f5ff] animate-pulse'
                  }`}
                />
                Step {activeStage}/6 · {stageLabel}
                {awaitingNextStep && (
                  <span className="px-2 py-0.5 rounded bg-[#a855f7]/25 text-[#e9d5ff] border border-[#a855f7]/40 text-[11px]">
                    STAGE {activeStage} READY — PAUSED (MANUAL MODE)
                  </span>
                )}
              </span>

              <div className="flex items-center gap-3">
                {awaitingNextStep && (
                  <button
                    type="button"
                    onClick={advanceStep}
                    className="flex items-center gap-1 px-3 py-1 rounded-md bg-[#00f5ff] text-[#090a0f] font-bold hover:brightness-110 transition-all shadow-[0_0_12px_rgba(0,245,255,0.4)]"
                  >
                    <span>Proceed to Stage {activeStage + 1}: {STAGE_TITLES[activeStage + 1]} (or press → / Space)</span>
                    <ChevronRight className="w-3.5 h-3.5 stroke-[2.5]" />
                  </button>
                )}
                <span className="text-slate-400">
                  {Math.round((activeStage / 6) * 100)}% Complete
                </span>
              </div>
            </div>
            <div className="mt-2 h-1 w-full rounded-full bg-white/10 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-[#00f5ff] to-[#a855f7] transition-all duration-700"
                style={{ width: `${(activeStage / 6) * 100}%` }}
              />
            </div>
          </section>
        )}

        {/* Main Content & Vertical Stepper Layout */}
        <div className="flex flex-col lg:flex-row items-start gap-6">
          {/* Active Stage Content (Left / Main) */}
          <section className="flex-1 w-full min-w-0 min-h-[500px]">
            {renderActiveStage()}
          </section>

          {/* Right Sidebar: Vertical Pipeline Stepper */}
          <aside className="w-full lg:w-64 shrink-0 lg:sticky lg:top-6 order-first lg:order-last">
            <PipelineStepper
              activeStage={activeStage}
              onStageClick={(stage) => setActiveStage(stage)}
              orientation="vertical"
            />
          </aside>
        </div>
      </main>
    </div>
  );
}
