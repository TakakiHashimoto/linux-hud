from pathlib import Path

UPTIME_PATH = Path("/proc/uptime")
MEMORY_PATH = Path("/proc/meminfo")

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

def get_memory_info():
    raw = MEMORY_PATH.read_text()
    for line in raw.splitlines():
        parts = line.split()
        print(len(parts), parts)
    one_item = raw.splitlines()[0]
    key, value, unit = one_item.split()
    key = key.removesuffix(":")
    print(key, int(value), unit)
    return raw

uptime = get_uptime_seconds()
mem_info = get_memory_info()
print("Uptime: ", format_uptime(uptime))
