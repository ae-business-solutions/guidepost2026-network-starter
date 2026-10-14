# Overview
Write a network unit test that catches the config that caused our last outage, anywhere in the network.

# What happened
`<one or two sentences about the outage, e.g. "A new access port was configured without storm control and a looped hub took down VLAN 30.">`

# Tools
- pytest, Python standard library only
- Look at `tests/test_bpduguard.py` in this repo and follow its style

# Test
- One new file: `tests/test_<what_it_checks>.py`
- Reads every config under `configs/` (no device access)
- Fails with a list of `<device> <interface or rule>` for every violation
- Skips cleanly when there are no configs of that type

# Architecture
- Keep it under 30 lines and readable by a network engineer who doesn't write Python
- Add a matching good and bad example in a comment at the top of the file
