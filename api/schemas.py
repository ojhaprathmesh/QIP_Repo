from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class SimulationRequest(BaseModel):
    resolution: int = Field(..., description="Resolution of the simulation")
    pattern: str = Field(..., description="Pattern to use for the simulation")
    encoding: str = Field(..., description="Encoding method to use")
    noise_channel: str = Field(..., description="Noise channel to apply")
    noise_rate: float = Field(..., description="Rate of noise to apply")
    shots: int = Field(..., description="Number of shots to run")
    denoise_method: str = Field(..., description="Denoising method to use")
    threshold: float = Field(..., description="Threshold for denoising")
    bit_depth: int = Field(8, description="Color register bit-depth q (8 or 4)")
    interpolation: str = Field("area", description="Downsampling kernel (area, bilinear, nearest)")
    gamma: float = Field(1.0, description="Radiometric gamma correction")
    step_mode: str = Field("auto", description="Execution flow mode: 'auto' or 'manual'")
    custom_pixels: Optional[List[List[float]]] = Field(None, description="Preprocessed custom real-world image matrix in [0, 1]")

class STAGE_STARTED(BaseModel):
    stage_id: int = Field(..., description="ID of the stage")
    stage_name: str = Field(..., description="Name of the stage")
    timestamp: float = Field(..., description="Timestamp when the stage started")

class CIRCUIT_COMPILED(BaseModel):
    qubits: int = Field(..., description="Number of qubits in the circuit")
    depth: int = Field(..., description="Depth of the circuit")
    total_gates: int = Field(..., description="Total number of gates in the circuit")
    cnot_count: int = Field(..., description="Number of CNOT gates in the circuit")

class STATEVECTOR_UPDATED(BaseModel):
    amplitudes: List[float] = Field(..., description="Amplitudes of the state vector")
    purity: float = Field(..., description="Purity of the state vector")

class SHOTS_ACCUMULATED(BaseModel):
    shots_completed: int = Field(..., description="Number of shots completed")
    total_shots: int = Field(..., description="Total number of shots")
    bitstring_counts: Dict[str, int] = Field(..., description="Counts of each bitstring")

class FRAME_RECONSTRUCTED(BaseModel):
    pixels: List[List[float]] = Field(..., description="Reconstructed pixel values")
    psnr: float = Field(..., description="Peak signal-to-noise ratio")
    ssim: float = Field(..., description="Structural similarity index")
    mse: float = Field(..., description="Mean squared error")
    fidelity: float = Field(0.95, description="Uhlmann-Jozsa quantum state fidelity F(rho, sigma)")
    classical_metrics: Optional[Dict[str, float]] = Field(None, description="Real classical filter PSNR/SSIM (median/gaussian/mean)")

class PHASE_CRIT_FOUND(BaseModel):
    p_crit: float = Field(..., description="Critical phase value")
    advantage_verdict: str = Field(..., description="Verdict on the quantum advantage")
