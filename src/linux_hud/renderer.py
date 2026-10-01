from linux_hud.models import HudSnapshot, MachineModel, NetworkRoute
from linux_hud.formatting import format_percent_bar, format_uptime, format_rate

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