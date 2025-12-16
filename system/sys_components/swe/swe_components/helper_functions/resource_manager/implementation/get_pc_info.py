import json
import psutil
import platform
import subprocess
from pathlib import Path
import pynvml
from sos_interfaces.if_system_configuration import resources_data
from system.sys_components.swe.swe_interfaces.implementation.if_resources import available_resources, fetch_resources_port

class resource_manager (fetch_resources_port):
    def __init__ (self):
        self.operating_machine_hw = self.operating_machine()
    def operating_machine (self) -> resources_data:
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
        
        return resources_data (
            gpu_count= data["gpu_count"],
            gpu_name= data["gpu_name"],                   # "RTX 5080"
            gpu_vram_gb= data["gpu_vram_gb"],              # 16.0
            gpu_compute_capability= data["gpu_compute_capability"],     # "8.9" or similar, if CUDA
            gpu_supports_fp16= data["gpu_supports_fp16"],
            gpu_supports_bf16= data["gpu_supports_bf16"],
            gpu_supports_cuda= data["gpu_supports_cuda"],

            cpu_model= data["cpu_model"],                  # "i9-14900KF"
            cpu_physical_cores= data["cpu_physical_cores"],
            cpu_logical_cores= data["cpu_logical_cores"] ,         # threads
            cpu_base_clock_ghz= None,       # optional but nice
            cpu_has_avx2= None,
            cpu_has_avx512= None,

            ram_total_gb= data["ram_total_gb"],
            ram_available_gb= data["ram_available_gb"] ,        # at runtime, optional in static config

            storage_type= data["storage_type"]  ,             # "nvme", "ssd", "hdd"
            storage_read_mb_s= data["storage_read_mb_s"] ,       # rough benchmark, optional
            storage_free_gb= data["storage_free_gb"]
        )
    
    def fetch_available_resources(self, resource_name: str, destination: Path) -> available_resources | None:
        # Get CPU usage over a 1-second interval
        cpu_usage = psutil.cpu_percent(interval=1)
        print(f"CPU Usage: {cpu_usage}%")

        # Get load averages (useful on Linux/macOS for overall workload trends)
        # Returns 1, 5, and 15 minute averages
        load_avg = psutil.getloadavg() 
        print(f"Load Averages (1, 5, 15 min): {load_avg}")

        memory = psutil.virtual_memory()

        # Convert bytes to GB for readability
        total_gb = round(memory.total / (1024**3), 2)
        available_gb = round(memory.available / (1024**3), 2)
        used_gb = round(memory.used / (1024**3), 2)

        print(f"Total RAM: {total_gb} GB")
        print(f"Available RAM: {available_gb} GB")
        print(f"Used RAM: {used_gb} GB")
        print(f"RAM Usage Percentage: {memory.percent}%")

        disk_usage = psutil.disk_usage('/') 

        # Convert bytes to GB
        total_gb = round(disk_usage.total / (1024**3), 2)
        used_gb = round(disk_usage.used / (1024**3), 2)
        free_gb = round(disk_usage.free / (1024**3), 2)

        print(f"Total Disk Space: {total_gb} GB")
        print(f"Used Disk Space: {used_gb} GB")
        print(f"Free Disk Space: {free_gb} GB")
        print(f"Disk Usage Percentage: {disk_usage.percent}%")

        net_io = psutil.net_io_counters()

        # Convert bytes to MB for readability
        bytes_sent_mb = round(net_io.bytes_sent / (1024**2), 2)
        bytes_received_mb = round(net_io.bytes_recv / (1024**2), 2)

        print(f"Bytes Sent: {bytes_sent_mb} MB")
        print(f"Bytes Received: {bytes_received_mb} MB")

        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0) # Get handle for the first GPU
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        free = info.free / 1024**2:.2f
        print(f"Total memory: {info.total / 1024**2:.2f} MiB")
        print(f"Free memory: {info.free / 1024**2:.2f} MiB")
        print(f"Used memory: {info.used / 1024**2:.2f} MiB")

        pynvml.nvmlShutdown()

        return available_resources (
            cpu = cpu_usage,
            ram = available_gb,
            rom = free_gb,
            gpu = {info.free / 1024**2:.2f}
        )