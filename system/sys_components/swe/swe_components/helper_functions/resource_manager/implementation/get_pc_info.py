import json
import psutil
import platform
import subprocess
from pathlib import Path

data = {}

# CPU
data["cpu_model"] = platform.processor()
data["cpu_physical_cores"] = psutil.cpu_count(logical=False)
data["cpu_logical_cores"] = psutil.cpu_count(logical=True)

# RAM
ram = psutil.virtual_memory()
data["ram_total_gb"] = round(ram.total / (1024 ** 3), 2)
data["ram_available_gb"] = round(ram.available / (1024 ** 3), 2)

# Storage (root)
disk = psutil.disk_usage("/")
data["storage_type"] = "NVMe/SSD"  # heuristic; you can refine detection
data["storage_read_mb_s"] = None  # advanced benchmark needed
data["storage_free_gb"] = round(disk.free / (1024 ** 3), 2)

# GPU info via nvidia-smi if NVIDIA present
try:
    smi = subprocess.check_output(["nvidia-smi", "--query-gpu=name,memory.total,compute_cap,driver_version",
                                   "--format=csv,noheader,nounits"], universal_newlines=True)
    gpu = smi.strip().split(", ")
    data["gpu_count"] = 1
    data["gpu_name"] = gpu[0]
    data["gpu_vram_gb"] = float(gpu[1]) / 1024
    data["gpu_compute_capability"] = gpu[2]
    data["gpu_supports_fp16"] = True
    data["gpu_supports_bf16"] = True
    data["gpu_supports_cuda"] = True
except Exception:
    data["gpu_count"] = 0
    data["gpu_name"] = None
    data["gpu_vram_gb"] = 0.0
    data["gpu_compute_capability"] = None
    data["gpu_supports_fp16"] = False
    data["gpu_supports_bf16"] = False
    data["gpu_supports_cuda"] = False

# Dump JSON
print(json.dumps(data, indent=2))
