from pathlib import Path

UPTIME_PATH = Path("/proc/uptime")

raw = UPTIME_PATH.read_text().strip()

uptime, idle_time = raw.split()

uptime_seconds = float(uptime)
idle_seconds = float(idle_time)

print(uptime_seconds, idle_seconds)