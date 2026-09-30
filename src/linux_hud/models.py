from dataclasses import dataclass
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
