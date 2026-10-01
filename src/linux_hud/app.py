import time
from linux_hud.models import (
    HudSnapshot,
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
from linux_hud.renderer import render_hud


ENTER_ALT_SCREEN = "\x1b[?1049h"
EXIT_ALT_SCREEN = "\x1b[?1049l"

HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"

HOME = "\x1b[H"
CLEAR = "\x1b[2J"

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