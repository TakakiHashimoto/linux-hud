# Linux HUD

A lightweight Linux terminal HUD for monitoring machine and network activity using data exposed by the Linux kernel and standard Linux networking tools.

## Features

- CPU usage
- Memory usage
- Network RX/TX rates
- IPv4 address and default gateway
- TCP established/listening socket counts
- UDP socket count
- System uptime
- Hostname and kernel information

## Requirements

- Linux
- Python 3.9+
- `iproute2`
  - `ip`
  - `ss`

## Installation

```bash
pipx install linux-hud
```
