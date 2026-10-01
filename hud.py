#!/usr/bin/env python3
# execute this file
#         ↓
# find python3 using PATH
#         ↓
# use that interpreter



import time
from linux_hud.models import (
    HudSnapshot,
    MachineModel,
    NetworkRoute,
)

from linux_hud.collectors import (
    get_cpu_counters,
    get_ipv4_addresses,
    get_machine_data,
    get_memory_info,
    get_network_counters,
    get_network_route,
    get_socket_counts,
    get_uptime_seconds,
)

from linux_hud.metrics import get_cpu_usage, get_network_rate
from linux_hud.formatting import format_percent_bar, format_rate, format_uptime

ENTER_ALT_SCREEN = "\x1b[?1049h"
EXIT_ALT_SCREEN = "\x1b[?1049l"

HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"

HOME = "\x1b[H"
CLEAR = "\x1b[2J"

def render_hud(
    snapshot: HudSnapshot,
    machine: MachineModel,
    route: NetworkRoute,
    ipv4_addresses: list[str],
) -> str:
    lines:list[str] = []

    cpu_bar = format_percent_bar(snapshot.cpu_usage_percent)
    ram_bar = format_percent_bar(snapshot.memory.usage_percent)

    lines.append(render_top("MACHINE"))
    lines.append(render_line(f"Host       {machine.hostname}"))
    lines.append(render_line(f"Kernel     {machine.kernel_release}"))
    lines.append(
        render_line(
            f"Uptime     {format_uptime(snapshot.uptime_seconds)}"
        )
    )
    lines.append(
        render_line(
            f"CPU        {cpu_bar} {snapshot.cpu_usage_percent:.1f}%"
        )
    )
    lines.append(
        render_line(
            f"RAM        {ram_bar} {snapshot.memory.usage_percent:.1f}%"
        )
    )
    lines.append(render_bottom())

    lines.append("")

    lines.append(render_top("NETWORK"))
    lines.append(render_line(f"Interface  {route.interface}"))
    lines.append(render_line(f"IPv4       {ipv4_addresses[0]}"))
    lines.append(render_line(f"Gateway    {route.gateway}"))
    lines.append(
        render_line(
            f"RX         {format_rate(snapshot.network_rate.rx_bytes_per_sec)}"
        )
    )
    lines.append(
        render_line(
            f"TX         {format_rate(snapshot.network_rate.tx_bytes_per_sec)}"
        )
    )
    lines.append(
        render_line(
            f"TCP ESTAB  {snapshot.socket_counts.tcp_established}"
        )
    )
    lines.append(
        render_line(
            f"TCP LISTEN {snapshot.socket_counts.tcp_listening}"
        )
    )
    lines.append(
        render_line(
            f"UDP        {snapshot.socket_counts.udp_sockets}"
        )
    )
    lines.append(render_bottom())

    return "\n".join(lines)

BOX_WIDTH = 60
def render_line(content: str) -> str:
    inner_width = BOX_WIDTH - 4
    return f"│ {content:<{inner_width}} │"

def render_top(title: str) -> str:
    label = f" {title} "
    return f"┌{label.center(BOX_WIDTH - 2, '─')}┐"

def render_bottom() -> str:
    return f"└{'─' * (BOX_WIDTH - 2)}┘"

def main():
    machine_info = get_machine_data()
    # network_interfaces = get_network_interfaces()
    network_route = get_network_route()
    ipv4_addresses = get_ipv4_addresses(network_route.interface)

    previous_counters = get_network_counters(network_route.interface)
    previous_cpu = get_cpu_counters()
    previous_time = time.monotonic()


    print(ENTER_ALT_SCREEN + HIDE_CURSOR + CLEAR, end="", flush=True)
    try:
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

            frame = render_hud(snapshot, machine=machine_info, route=network_route, ipv4_addresses=ipv4_addresses)
            print(HOME + frame, end="", flush=True)

    except KeyboardInterrupt:
        pass
    finally:
        print(SHOW_CURSOR + EXIT_ALT_SCREEN, end="", flush=True)

if __name__ == "__main__":
       main()