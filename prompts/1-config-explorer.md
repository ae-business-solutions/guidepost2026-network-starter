# Overview
Read a folder of switch and router configs and produce a single-page HTML report for exploring them and checking them against best practices.

# Tools
- Python 3, standard library only
- Any UI approach you like, but the output must be one self-contained HTML file: no CDNs, no external calls
- Make it look good

# Inputs
- A folder of running configs, one file per device (Cisco IOS/NX-OS and Arista EOS style), for example the `configs/` folder from `collect.py`
- The device name is the file name

# Output
One HTML file, named `config-explorer-<date>.html`, with:
- **Devices**: one row per device with model or platform hints, interface count, VLANs, routing protocols
- **Search**: free text across every config, with the matching lines and their device
- **Interfaces**: every interface with description, mode, VLANs and shutdown state, filterable
- **Issues**: findings with a severity and a one-line reason:
  - no AAA, or local-only login
  - fewer than two NTP servers
  - Telnet or HTTP management enabled; SSH v1
  - SNMP v1/v2c communities
  - no remote logging
  - access ports without BPDU guard; unused ports not shut down
  - interfaces without descriptions

# Architecture
- One script: read the folder, write the HTML file, exit
- Never prints or embeds secrets: mask passwords, keys and SNMP communities in the report
- The configs stay on my machine; only this prompt goes to the AI
