def format_rate(bytes_per_second: float) -> str:
    if bytes_per_second < 1024:
        return f"{bytes_per_second:.2f} B/s"
    
    if bytes_per_second < 1024 * 1024:
        return f"{bytes_per_second / 1024:.2f} KiB/s"
        
    return f"{bytes_per_second / (1024 * 1024):.2f} MiB/s"

def format_uptime(seconds:float) -> str:
    minutes = int(seconds) // 60
    remaining_seconds = int(seconds) % 60
    hours = minutes // 60
    real_minute = minutes % 60

    return f"{hours}h {real_minute}m {remaining_seconds}s"

def format_percent_bar(percent: float, width: int = 20) -> str:
    percent = max(0.0, min(percent, 100.0))

    filled = int((percent / 100) * width)
    empty = width - filled

    return "█" * filled + "░" * empty
