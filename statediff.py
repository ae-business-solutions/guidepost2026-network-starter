"""Step 5: capture a switch's state before and after a change, then diff it.

    python statediff.py capture sw1 before.json     # read-only show commands over eAPI
    # ... upgrade, reboot or change the switch ...
    python statediff.py capture sw1 after.json
    python statediff.py diff before.json after.json # exit 1 if anything needs a look

Arista EOS over eAPI, read-only. Credentials come from NET_USERNAME / NET_PASSWORD,
or you are prompted; they are never saved. Wrap it around any change, not just upgrades.
To add another platform, give AI prompts/5-upgrade.md.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import urllib3

COMMANDS = [
    "show version",
    "show interfaces description",
    "show ip route vrf all summary",
    "show bgp summary vrf all",
    "show lldp neighbors detail",
    "show mlag",
    "show ip arp vrf all",
    "show mac address-table",
]
DROP_TOLERANCE = 0.10  # route, ARP and MAC counts may fall this much before we call it a problem


# --------------------------------------------------------------------------- capture


def eapi(host: str, user: str, password: str, command: str, verify: bool) -> dict | None:
    """Run one show command; None if this switch doesn't support it."""
    body = {
        "jsonrpc": "2.0",
        "method": "runCmds",
        "params": {"version": 1, "cmds": [command], "format": "json"},
        "id": 1,
    }
    reply = requests.post(f"https://{host}/command-api", json=body, auth=(user, password), verify=verify, timeout=60)
    if reply.status_code == 401:
        raise SystemExit(f"{host}: login failed")
    reply.raise_for_status()
    data = reply.json()
    return None if "error" in data else data["result"][0]


def summarize(raw: dict) -> dict:
    """Reduce raw command output to the facts we compare."""
    version = raw.get("show version") or {}
    mem_total = version.get("memTotal") or 0
    interfaces = (raw.get("show interfaces description") or {}).get("interfaceDescriptions", {})
    vrfs = (raw.get("show ip route vrf all summary") or {}).get("vrfs", {})
    bgp = (raw.get("show bgp summary vrf all") or {}).get("vrfs", {})
    lldp = (raw.get("show lldp neighbors detail") or {}).get("lldpNeighbors", {})
    arp = raw.get("show ip arp vrf all")
    mac = raw.get("show mac address-table")
    return {
        "version": version.get("version"),
        "memory_used_pct": round(100 * (1 - version.get("memFree", 0) / mem_total)) if mem_total else None,
        "interfaces_up": sorted(i for i, d in interfaces.items() if d.get("lineProtocolStatus") == "up"),
        "routes": sum(v.get("totalRoutes", 0) for v in vrfs.values()) if vrfs else None,
        "bgp_established": sorted(
            f"{vrf}/{peer}"
            for vrf, v in bgp.items()
            for peer, p in v.get("peers", {}).items()
            if p.get("peerState") == "Established"
        ),
        "lldp_neighbors": sorted(
            f"{port} -> {n.get('systemName')}" for port, d in lldp.items() for n in d.get("lldpNeighborInfo", [])
        ),
        "mlag": (raw.get("show mlag") or {}).get("state"),
        "arp_entries": _count(arp, "vrfs", "ipV4Neighbors"),
        "mac_entries": len(mac["unicastTable"]["tableEntries"]) if mac and "unicastTable" in mac else None,
    }


def _count(output: dict | None, outer: str, inner: str) -> int | None:
    if not output:
        return None
    if outer in output:  # per-VRF output
        return sum(len(v.get(inner, [])) for v in output[outer].values())
    return len(output[inner]) if inner in output else None


def capture(host: str, out: str, verify: bool) -> None:
    user = os.environ.get("NET_USERNAME") or input("Username: ")
    password = os.environ.get("NET_PASSWORD") or getpass.getpass(f"Password for {user}: ")
    raw = {cmd: eapi(host, user, password, cmd, verify) for cmd in COMMANDS}
    state = {
        "host": host,
        "captured": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "facts": summarize(raw),
        "raw": raw,
    }
    Path(out).write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    facts = state["facts"]
    print(
        f"✓ {host}: {facts['version']}, {len(facts['interfaces_up'])} interfaces up, "
        f"{len(facts['bgp_established'])} BGP peers established -> {out}"
    )


# --------------------------------------------------------------------------- diff


def compare(before: dict, after: dict) -> list[tuple[str, str, str, str, str]]:
    """Rows of (fact, before, after, status, detail). status is ok, info or CHECK."""
    rows = []

    def as_set(name: str, label: str) -> None:
        old, new = set(before.get(name) or []), set(after.get(name) or [])
        lost = sorted(old - new)
        status = "CHECK" if lost else "ok"
        rows.append(
            (label, str(len(old)), str(len(new)), status, ", ".join(lost[:3]) + (" ..." if len(lost) > 3 else ""))
        )

    def as_count(name: str, label: str) -> None:
        old, new = before.get(name), after.get(name)
        if old is None or new is None:
            rows.append((label, _fmt(old), _fmt(new), "info", "not available"))
            return
        dropped = new < old * (1 - DROP_TOLERANCE)
        rows.append(
            (label, _fmt(old), _fmt(new), "CHECK" if dropped else "ok", f"{(new - old) / old:+.0%}" if dropped else "")
        )

    old_v, new_v = before.get("version"), after.get("version")
    rows.append(("Version", str(old_v), str(new_v), "info", "changed" if old_v != new_v else ""))
    as_set("interfaces_up", "Interfaces up")
    as_set("bgp_established", "BGP peers established")
    as_set("lldp_neighbors", "LLDP neighbors")
    as_count("routes", "Routes")
    as_count("arp_entries", "ARP entries")
    as_count("mac_entries", "MAC entries")
    old_m, new_m = before.get("mlag"), after.get("mlag")
    mlag_lost = old_m == "active" and new_m != "active"
    rows.append(("MLAG", str(old_m), str(new_m), "CHECK" if mlag_lost else "ok", "was active" if mlag_lost else ""))
    rows.append(("Memory used %", _fmt(before.get("memory_used_pct")), _fmt(after.get("memory_used_pct")), "info", ""))
    return rows


def _fmt(value) -> str:
    return "n/a" if value is None else f"{value:,}" if isinstance(value, int) else str(value)


def diff(before_file: str, after_file: str) -> int:
    before, after = json.loads(Path(before_file).read_text()), json.loads(Path(after_file).read_text())
    rows = compare(before["facts"], after["facts"])
    print(f"{before['host']:<24}{'before':>10}{'after':>10}")
    for label, old, new, status, detail in rows:
        mark = f"  CHECK: {detail}" if status == "CHECK" else f"  {detail}" if detail else ""
        print(f"{label:<24}{old:>10}{new:>10}{mark}")
    checks = [r for r in rows if r[3] == "CHECK"]
    print(f"\nVerdict: {'HOLD, ' + str(len(checks)) + ' thing(s) to look at' if checks else 'OK, nothing to look at'}.")
    return 1 if checks else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("capture", help="save the switch's state to a JSON file")
    p.add_argument("host")
    p.add_argument("out")
    p.add_argument("--insecure", action="store_true", help="skip TLS verification (lab self-signed certs)")
    p = sub.add_parser("diff", help="compare two captures")
    p.add_argument("before")
    p.add_argument("after")
    args = parser.parse_args()

    if args.command == "capture":
        if args.insecure:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        capture(args.host, args.out, verify=not args.insecure)
        return 0
    return diff(args.before, args.after)


if __name__ == "__main__":
    sys.exit(main())
