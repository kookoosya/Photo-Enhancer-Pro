"""Hardware and performance utilities."""

from __future__ import annotations

import multiprocessing as mp
import os
from dataclasses import dataclass

import cv2
import psutil


@dataclass
class SystemInfo:
    """System hardware information."""

    cpu_count: int
    memory_gb: float
    cuda_available: bool
    gpu_name: str | None


def get_cpu_count() -> int:
    """Get optimal worker count."""
    return max(1, min(mp.cpu_count(), os.cpu_count() or 4))


def get_memory_gb() -> float:
    """Get available system memory in GB."""
    return psutil.virtual_memory().available / (1024 ** 3)


def check_cuda() -> tuple[bool, str | None]:
    """Check CUDA availability via OpenCV and PyTorch."""
    cuda_ok = False
    gpu_name: str | None = None

    try:
        count = cv2.cuda.getCudaEnabledDeviceCount()  # type: ignore[attr-defined]
        if count > 0:
            cuda_ok = True
    except Exception:
        pass

    try:
        import torch

        if torch.cuda.is_available():
            cuda_ok = True
            gpu_name = torch.cuda.get_device_name(0)
    except ImportError:
        pass

    return cuda_ok, gpu_name


def get_system_info() -> SystemInfo:
    """Collect system information."""
    cuda_ok, gpu_name = check_cuda()
    return SystemInfo(
        cpu_count=get_cpu_count(),
        memory_gb=round(get_memory_gb(), 2),
        cuda_available=cuda_ok,
        gpu_name=gpu_name,
    )


def get_gpu_usage() -> dict[str, float]:
    """Get GPU utilization if available."""
    result: dict[str, float] = {"gpu_percent": 0.0, "memory_percent": 0.0}
    try:
        import torch

        if torch.cuda.is_available():
            result["memory_percent"] = (
                torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated() * 100
                if torch.cuda.max_memory_allocated() > 0
                else 0.0
            )
    except ImportError:
        pass
    try:
        result["gpu_percent"] = psutil.cpu_percent()
    except Exception:
        pass
    return result
