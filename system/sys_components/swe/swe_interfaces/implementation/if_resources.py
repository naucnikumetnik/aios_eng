from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

@dataclass(frozen=True)
class resources_data:
    gpu_count: int
    gpu_name: str                   # "RTX 5080"
    gpu_vram_gb: float              # 16.0
    gpu_compute_capability: str     # "8.9" or similar, if CUDA
    gpu_supports_fp16: bool
    gpu_supports_bf16: bool
    gpu_supports_cuda: bool

    cpu_model: str                  # "i9-14900KF"
    cpu_physical_cores: int
    cpu_logical_cores: int          # threads
    cpu_base_clock_ghz: float       # optional but nice
    cpu_has_avx2: bool
    cpu_has_avx512: bool

    ram_total_gb: float
    ram_available_gb: float         # at runtime, optional in static config

    storage_type: str               # "nvme", "ssd", "hdd"
    storage_read_mb_s: float        # rough benchmark, optional
    storage_free_gb: float

class fetch_resources_port (Protocol):
    def fetch_available_resources (self, resource_name: str, destination: Path) -> resources:
        ...