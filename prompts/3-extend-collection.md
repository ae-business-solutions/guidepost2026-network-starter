# Overview
Extend `collect.py` in this repo to back up another kind of device.

# Tools
- Python 3; keep the existing structure of `collect.py`
- Netmiko for CLI devices, or the vendor's REST/XML API if it has one

# Change
- Add support for `<platform>`, for example Fortinet FortiGate (`fortinet`) or Cisco ASA (`cisco_asa`)
- Use the read-only command or API call that returns the full running configuration
- Save it under `configs/<site>/<device>.cfg` like the others

# Architecture
- Read-only: no configuration mode, no changes
- Run the output through `scrub.py` before writing it, and add patterns to `scrub.py` for any new secret formats this platform prints
- Credentials still come only from `NET_USERNAME` / `NET_PASSWORD` or a prompt
- Add one entry to `inventory.yml` as an example
