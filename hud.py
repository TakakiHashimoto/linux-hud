from dataclasses import dataclass
from pathlib import Path
import os
import subprocess
import json

UPTIME_PATH = Path("/proc/uptime")
MEMORY_PATH = Path("/proc/meminfo")
NETWORK_INTERFACE_PATH = Path("/sys/class/net")

@dataclass
class MemoryStats:
    total_bytes: int
    available_bytes: int
    used_bytes: int
    usage_percent: float
    swap_total_bytes: int
    swap_used_bytes: int

@dataclass
class MachineModel:
    hostname: str
    kernel_release: str
    architecture: str

@dataclass
class NetworkInterface:
    name: str
    mac_addr: str
    state: str
    mtu: int

@dataclass
class NetworkRoute:
    interface: str
    gateway:str

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

def get_machine_data():
    info = os.uname()
    machine_info = MachineModel(hostname=info.nodename, kernel_release=info.release, architecture=info.machine)
    return machine_info

def get_network_interfaces() -> list[NetworkInterface]:
    network_info : list[NetworkInterface] = []
    for item in NETWORK_INTERFACE_PATH.iterdir():
        network_interface = NetworkInterface(item.name, mac_addr=(item / "address").read_text().strip(), state=(item / "operstate").read_text().strip(), mtu=int((item / "mtu").read_text().strip()))
        network_info.append(network_interface)

    return network_info

def get_network_route():
    return


uptime = get_uptime_seconds()
mem_info = get_memory_info()
machine_info = get_machine_data()
network_interfaces = get_network_interfaces()
print("Uptime: ", format_uptime(uptime))
print("memory info: ", mem_info)
print("machine info: ", machine_info)
print("network interfaces: ", network_interfaces)
