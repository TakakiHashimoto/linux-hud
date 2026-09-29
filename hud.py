from dataclasses import dataclass
from pathlib import Path
import os
import subprocess
import json
import time

UPTIME_PATH = Path("/proc/uptime")
MEMORY_PATH = Path("/proc/meminfo")
NETWORK_INTERFACE_PATH = Path("/sys/class/net")
CPU_STAT_PATH = Path("/proc/stat")

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

@dataclass
class CpuCounters:
    user: int
    nice: int
    system: int
    idle: int
    iowait: int
    irq: int
    softirq: int
    steal: int

@dataclass
class SocketCounts:
    tcp_established: int
    tcp_listening: int
    udp_sockets: int

@dataclass
class HudSnapshot:
    uptime_seconds: float
    memory: MemoryStats
    cpu_usage_percent: float
    network_rate: NetworkRate
    socket_counts: SocketCounts


def format_rate(bytes_per_second: float) -> str:
    if bytes_per_second < 1024:
        return f"{bytes_per_second} B/s"
    
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

def get_cpu_counters() -> CpuCounters:
    cpu_columns = CPU_STAT_PATH.read_text().splitlines()
    cpu_stats = cpu_columns[0].split()
    cpu_counters = CpuCounters(user=int(cpu_stats[1]), nice=int(cpu_stats[2]), system=int(cpu_stats[3]), idle=int(cpu_stats[4]),iowait=int(cpu_stats[5]), irq=int(cpu_stats[6]), softirq=int(cpu_stats[7]), steal=int(cpu_stats[8]))
    return cpu_counters

def get_cpu_usage(prev:CpuCounters, current:CpuCounters):
    prev_total = prev.system + prev.user + prev.nice + prev.idle + prev.iowait + prev.irq + prev.softirq + prev.steal
    current_total = current.system + current.user + current.nice + current.idle + current.iowait + current.irq + current.softirq + current.steal
    total_delta = current_total - prev_total
    prev_none_busy = prev.idle + prev.iowait
    current_none_busy = current.idle + current.iowait
    total_none_busy = current_none_busy - prev_none_busy
    total_used =((total_delta - total_none_busy) / total_delta) * 100

    return total_used

def get_socket_counts() -> SocketCounts:
    counts = {"tcp_established" : 0, "tcp_listening" : 0, "udp_sockets" : 0}

    tcp_argument_lists = ["ss", "-Htan"]
    udp_arguments_list = ["ss", "-Huan"]

    tcp_sockets = subprocess.run(tcp_argument_lists,
        capture_output=True,
        text=True,
        check=True,
    )
    udp_sockets = subprocess.run(udp_arguments_list,
        capture_output=True,
        text=True,
        check=True,                         
    )

    tcp_socket_lists = tcp_sockets.stdout.splitlines()
    udp_socket_lists = udp_sockets.stdout.splitlines()

    for socket in tcp_socket_lists:
        if not socket.strip():
            continue
        status = socket.split()[0]
        if status == "LISTEN":
            counts["tcp_listening"] += 1
        elif status == "ESTAB":
            counts["tcp_established"] += 1

    counts["udp_sockets"] = sum(1 for line in udp_socket_lists if line.strip())

    return SocketCounts(tcp_established=counts["tcp_established"], tcp_listening=counts["tcp_listening"], udp_sockets=counts["udp_sockets"])


machine_info = get_machine_data()
network_interfaces = get_network_interfaces()
network_route = get_network_route()
ipv4_addresses = get_ipv4_addresses(network_route.interface)

previous_counters = get_network_counters(network_route.interface)
previous_cpu = get_cpu_counters()
previous_time = time.monotonic()

while True:
    
    time.sleep(1)

    current_time = time.monotonic()
    current_counters = get_network_counters(network_route.interface)
    current_cpu = get_cpu_counters()

    elapsed_seconds = current_time - previous_time

    network_rate = get_network_rate(
        previous_counters,
        current_counters,
        elapsed_seconds,
    )
    cpu_usage = get_cpu_usage(previous_cpu, current_cpu)

    uptime = get_uptime_seconds()
    mem_info = get_memory_info()
    socket_counts = get_socket_counts()

    snapshot = HudSnapshot(
        uptime_seconds=uptime,
        memory=mem_info,
        cpu_usage_percent=cpu_usage,
        network_rate=network_rate,
        socket_counts=socket_counts,
    )

    previous_time = current_time
    previous_counters = current_counters
    previous_cpu = current_cpu

    print(f"CPU:        {cpu_usage:.1f}%")
    print(f"RAM:        {mem_info.usage_percent:.1f}%")
    print(f"RX:         {format_rate(network_rate.rx_bytes_per_sec)}")
    print(f"TX:         {format_rate(network_rate.tx_bytes_per_sec)}")
    print(f"TCP ESTAB:  {socket_counts.tcp_established}")
    print(f"TCP LISTEN: {socket_counts.tcp_listening}")
    print(f"UDP:        {socket_counts.udp_sockets}")
    print(f"Uptime:     {format_uptime(uptime)}")
    print("------------------------------")
