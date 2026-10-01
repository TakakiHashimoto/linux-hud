from pathlib import Path
import os
import subprocess
import json
from linux_hud.models import (
    CpuCounters,
    MachineModel,
    MemoryStats,
    NetworkCounters,
    NetworkInterface,
    NetworkRoute,
    SocketCounts,
)

UPTIME_PATH = Path("/proc/uptime")
MEMORY_PATH = Path("/proc/meminfo")
NETWORK_INTERFACE_PATH = Path("/sys/class/net")
CPU_STAT_PATH = Path("/proc/stat")

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

def get_cpu_counters() -> CpuCounters:
    cpu_columns = CPU_STAT_PATH.read_text().splitlines()
    cpu_stats = cpu_columns[0].split()
    cpu_counters = CpuCounters(user=int(cpu_stats[1]), nice=int(cpu_stats[2]), system=int(cpu_stats[3]), idle=int(cpu_stats[4]),iowait=int(cpu_stats[5]), irq=int(cpu_stats[6]), softirq=int(cpu_stats[7]), steal=int(cpu_stats[8]))
    return cpu_counters

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
