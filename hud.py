from dataclasses import dataclass
from pathlib import Path
import os
import subprocess
import json
import time

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

@dataclass
class NetworkCounters:
    rx_bytes: int
    tx_bytes: int

@dataclass
class NetworkRate:
    rx_bytes_per_sec: float
    tx_bytes_per_sec: float

def format_rate(bytes_per_second: float) -> str:
    if bytes_per_second < 1024:
        return f"{bytes_per_second} b/s"
    
    if bytes_per_second < 1024 * 1024:
        return f"{bytes_per_second / 1024} KiB/s"
        
    return f"{bytes_per_second / (1024 * 1024)} MiB/s"

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

def get_network_route() -> NetworkRoute:
    argument_lists = ["ip", "-j", "route", "show", "default"]
    result = subprocess.run(
        argument_lists,
        capture_output=True,
        text=True,
        check=True,
    )
    routes = json.loads(result.stdout)
    route = routes[0]
    network_route = NetworkRoute(interface=route["dev"], gateway=route["gateway"])
    return network_route

def get_ipv4_addresses(interface: str) -> list[str]:
    argument_lists = ["ip", "-j", "addr", "show", "dev", interface]
    ipv4_addrs : list[str] = []
    result = subprocess.run(
        argument_lists,
        capture_output=True,
        text=True,
        check=True,
    )
    interface_info = json.loads(result.stdout)
    for address in interface_info[0]["addr_info"]:
        if address["family"] == "inet":
            ipv4_addrs.append(address["local"])
    return ipv4_addrs

def get_network_counters(interface: str) -> NetworkCounters:
    path = NETWORK_INTERFACE_PATH / interface / "statistics"
    rx = (path / "rx_bytes").read_text().strip()
    tx = (path / "tx_bytes").read_text().strip()
    return NetworkCounters(rx_bytes=int(rx), tx_bytes=int(tx))

def get_network_rate(previous: NetworkCounters, current: NetworkCounters, elapsed_seconds: float) -> NetworkRate:
    rx_diff =  current.rx_bytes - previous.rx_bytes
    tx_diff = current.tx_bytes - previous.tx_bytes

    rx_rate = (rx_diff / elapsed_seconds)
    tx_rate = (tx_diff / elapsed_seconds)
    return NetworkRate(rx_bytes_per_sec=rx_rate, tx_bytes_per_sec=tx_rate)

uptime = get_uptime_seconds()
mem_info = get_memory_info()
machine_info = get_machine_data()
network_interfaces = get_network_interfaces()
network_route = get_network_route()
ipv4_addresses = get_ipv4_addresses(network_route.interface)
network_counters = get_network_counters(network_route.interface)

first_time = time.monotonic()
previous_counters = get_network_counters(network_route.interface)

time.sleep(1)

current_time = time.monotonic()
current_counters = get_network_counters(network_route.interface)

elapsed_seconds = current_time - first_time

network_rate = get_network_rate(
    previous_counters,
    current_counters,
    elapsed_seconds,
)

