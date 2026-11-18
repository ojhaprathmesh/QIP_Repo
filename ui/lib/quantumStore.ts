import { create } from 'zustand';
import { PipelineState, QuantumEvent } from './types';

export const useQuantumStore = create<PipelineState>((set) => ({
  activeStage: 1,
  config: {
    resolution: 16,
    pattern: 'cameraman',
    encoding: 'neqr',
    noise_rate: 0.003,
    bit_depth: 8,
    interpolation: 'area',
    gamma: 1.0,
    contrast_stretch: true,
    custom_pixels: null,
    custom_image_name: null,
  },
  setConfig: (config) => set((state) => ({ config: { ...state.config, ...config } })),
  circuitInfo: null,
  statevector: null,
  shotsProgress: null,
  frameResult: null,
  phaseCrit: null,
  isRunning: false,
  events: [],

  setActiveStage: (stage: number) => set({ activeStage: stage }),

  startSimulation: () =>
    set({
      isRunning: true,
      circuitInfo: null,
      statevector: null,
      shotsProgress: null,
      frameResult: null,
      phaseCrit: null,
      events: [],
      activeStage: 1,
    }),

  resetPipeline: () =>
    set({
      activeStage: 1,
      circuitInfo: null,
      statevector: null,
      shotsProgress: null,
      frameResult: null,
      phaseCrit: null,
      isRunning: false,
      events: [],
    }),

  handleEvent: (event: QuantumEvent) =>
    set((state) => {
      const updatedEvents = [...state.events, event];

      switch (event.event_type) {
        case 'STAGE_STARTED':
          return {
            events: updatedEvents,
            activeStage: event.stage_id,
          };
        case 'CIRCUIT_COMPILED':
          return {
            events: updatedEvents,
            circuitInfo: event,
          };
        case 'STATEVECTOR_UPDATED':
          return {
            events: updatedEvents,
            statevector: event,
          };
        case 'SHOTS_ACCUMULATED':
          return {
            events: updatedEvents,
            shotsProgress: event,
          };
        case 'FRAME_RECONSTRUCTED':
          return {
            events: updatedEvents,
            frameResult: event,
          };
        case 'PHASE_CRIT_FOUND':
          return {
            events: updatedEvents,
            phaseCrit: event,
            isRunning: false,
          };
        default:
          return { events: updatedEvents };
      }
    }),
}));
