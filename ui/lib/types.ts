export interface SimulationRequest {
  resolution: number;
  pattern: string;
  encoding: 'frqi' | 'neqr' | string;
  noise_channel: string;
  noise_rate: number;
  shots: number;
  denoise_method: string;
  threshold: number;
  bit_depth?: number;
  interpolation?: string;
  gamma?: number;
  custom_pixels?: number[][] | null;
}

export interface StageStartedEvent {
  event_type: 'STAGE_STARTED';
  stage_id: number;
  stage_name: string;
  timestamp: number;
}

export interface CircuitCompiledEvent {
  event_type: 'CIRCUIT_COMPILED';
  qubits: number;
  depth: number;
  total_gates: number;
  cnot_count: number;
}

export interface StatevectorUpdatedEvent {
  event_type: 'STATEVECTOR_UPDATED';
  amplitudes: number[];
  purity: number;
}

export interface ShotsAccumulatedEvent {
  event_type: 'SHOTS_ACCUMULATED';
  shots_completed: number;
  total_shots: number;
  bitstring_counts: Record<string, number>;
}

export interface FrameReconstructedEvent {
  event_type: 'FRAME_RECONSTRUCTED';
  pixels: number[][];
  psnr: number;
  ssim: number;
  mse: number;
  fidelity?: number;
}

export interface PhaseCritFoundEvent {
  event_type: 'PHASE_CRIT_FOUND';
  p_crit: number;
  advantage_verdict: string;
}

export type QuantumEvent =
  | StageStartedEvent
  | CircuitCompiledEvent
  | StatevectorUpdatedEvent
  | ShotsAccumulatedEvent
  | FrameReconstructedEvent
  | PhaseCritFoundEvent;

export interface IngestionConfig {
  resolution: number;
  pattern: string;
  encoding: 'frqi' | 'neqr';
  noise_rate: number;
  bit_depth: 4 | 8;
  interpolation: 'area' | 'bilinear' | 'nearest';
  gamma: number;
  contrast_stretch: boolean;
  custom_pixels: number[][] | null;
  custom_image_name: string | null;
}

export interface PipelineState {
  activeStage: number;
  config: IngestionConfig;
  setConfig: (config: Partial<IngestionConfig>) => void;
  circuitInfo: CircuitCompiledEvent | null;
  statevector: StatevectorUpdatedEvent | null;
  shotsProgress: ShotsAccumulatedEvent | null;
  frameResult: FrameReconstructedEvent | null;
  phaseCrit: PhaseCritFoundEvent | null;
  isRunning: boolean;
  events: QuantumEvent[];
  setActiveStage: (stage: number) => void;
  handleEvent: (event: QuantumEvent) => void;
  startSimulation: () => void;
  resetPipeline: () => void;
}
