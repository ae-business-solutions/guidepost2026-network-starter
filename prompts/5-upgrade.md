# Overview
Automate a software upgrade of one HA pair, and prove nothing broke with a before-and-after state diff.

# Tools
- Python 3
- `<platform>` and its API, for example Palo Alto PAN-OS XML API or Arista eAPI
- `statediff.py` from this repo for the state capture and diff; extend it for `<platform>` if needed

# Steps
1. Capture state on both members: version, HA state, sessions, CPU and memory, routes, ARP, interfaces, BGP neighbors
2. Pre-checks: target image present and verified, disk space, HA in sync, config saved; stop if any fail
3. Upgrade the passive member, wait for it to rejoin, fail over, then upgrade the other member
4. Capture state again
5. Diff before and after; print a verdict and stop with a non-zero exit if anything needs a look

# Inputs
- The two device addresses, the target version, and a username
- Prompt for the password; never save credentials

# Architecture
- `--dry-run` runs steps 1, 2 and 4 only and changes nothing
- Ask for a typed `yes` before step 3
- Log every command sent and every result to a timestamped file
- Rehearse in the lab before the first production run
