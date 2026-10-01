from linux_hud.models import NetworkRate, NetworkCounters,CpuCounters

def get_network_rate(previous: NetworkCounters, current: NetworkCounters, elapsed_seconds: float) -> NetworkRate:
    rx_diff =  current.rx_bytes - previous.rx_bytes
    tx_diff = current.tx_bytes - previous.tx_bytes

    rx_rate = (rx_diff / elapsed_seconds)
    tx_rate = (tx_diff / elapsed_seconds)
    return NetworkRate(rx_bytes_per_sec=rx_rate, tx_bytes_per_sec=tx_rate)

def get_cpu_usage(prev:CpuCounters, current:CpuCounters) -> float:
    prev_total = prev.system + prev.user + prev.nice + prev.idle + prev.iowait + prev.irq + prev.softirq + prev.steal
    current_total = current.system + current.user + current.nice + current.idle + current.iowait + current.irq + current.softirq + current.steal
    total_delta = current_total - prev_total
    prev_none_busy = prev.idle + prev.iowait
    current_none_busy = current.idle + current.iowait
    total_none_busy = current_none_busy - prev_none_busy
    total_used =((total_delta - total_none_busy) / total_delta) * 100

    return total_used