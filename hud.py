from dataclasses import dataclass
from pathlib import Path

UPTIME_PATH = Path("/proc/uptime")
MEMORY_PATH = Path("/proc/meminfo")

@dataclass
class MemoryStats:
    total_bytes: int
    available_bytes: int
    used_bytes: int
    usage_percent: float
    swap_total_bytes: int
    swap_used_bytes: int

def format_uptime(seconds:float) -> str:
    minutes = int(seconds) // 60
    remaining_seconds = int(seconds) % 60
    hours = minutes // 60
    real_minute = minutes % 60

    return f"{hours}h {real_minute}m {remaining_seconds}s"


def get_uptime_seconds() -> float:
    raw = UPTIME_PATH.read_text().strip()
    uptime_text, _ = raw.split()

    return float(uptime_text)

def get_memory_info() -> MemoryStats:
    raw = MEMORY_PATH.read_text()
    data: dict[str, int] = {}
    wanted_fields = {
        "MemTotal",
        "MemAvailable",
        "SwapTotal",
        "SwapFree",
    }

    for line in raw.splitlines():
        if len(line.split()) == 3:
            key, value, _unit = line.split()
            if key[:-1] in wanted_fields:
                data[key[:-1]] =int(value) * 1024

    used = data["MemTotal"] - data["MemAvailable"]
    used_percent = used / data["MemTotal"] * 100
    swap_used = data["SwapTotal"] - data["SwapFree"]

    memory_stats = MemoryStats(total_bytes=data["MemTotal"],
        available_bytes = data["MemAvailable"],
        used_bytes=used,
        usage_percent=used_percent,
        swap_total_bytes=data["SwapTotal"],
        swap_used_bytes=swap_used)
        
    return memory_stats

uptime = get_uptime_seconds()
mem_info = get_memory_info()
print("Uptime: ", format_uptime(uptime))
print("memory info: ", mem_info)
