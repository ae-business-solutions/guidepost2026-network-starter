"""Step 3: back up running configs, read-only, into configs/<site>/<device>.<ext>.

    python collect.py                       # every device in inventory.yml
    python collect.py --only sw1 --insecure

Credentials come from NET_USERNAME / NET_PASSWORD, or you are prompted. They are never
written to disk. Use an account that can only read: on Arista EOS, role network-operator.

Every config goes through scrub.py before it is saved, so secrets stay out of git.
Platforms: anything Netmiko supports over SSH (see COMMANDS), plus Palo Alto PAN-OS
over its XML API. Exits non-zero if any device fails; the rest are still saved.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
import urllib3
import yaml

from scrub import scrub

# Netmiko device_type -> read-only command that prints the full running config.
COMMANDS = {
    "arista_eos": "show running-config",
    "cisco_ios": "show running-config",
    "cisco_xe": "show running-config",
    "cisco_nxos": "show running-config",
    "cisco_asa": "show running-config",
    "juniper_junos": "show configuration | display set",
}


def credentials() -> tuple[str, str]:
    user = os.environ.get("NET_USERNAME") or input("Username: ")
    password = os.environ.get("NET_PASSWORD") or getpass.getpass(f"Password for {user}: ")
    return user, password


def collect_cli(device: dict, user: str, password: str) -> str:
    from netmiko import ConnectHandler  # imported here so the PAN-OS-only path needs no Netmiko

    # secret: the enable password, if the platform asks for one (often the same login with TACACS).
    params = {
        "device_type": device["platform"],
        "host": device["host"],
        "username": user,
        "password": password,
        "secret": password,
    }
    with ConnectHandler(**params) as conn:
        if not conn.check_enable_mode():
            conn.enable()
        return conn.send_command(COMMANDS[device["platform"]], read_timeout=120)


def collect_panos(device: dict, user: str, password: str, verify: bool) -> str:
    url = f"https://{device['host']}/api/"
    # POST keeps the password out of URLs and proxy logs.
    reply = requests.post(url, data={"type": "keygen", "user": user, "password": password}, verify=verify, timeout=30)
    reply.raise_for_status()
    key = ET.fromstring(reply.text).findtext(".//key")
    if not key:
        raise RuntimeError("login failed (no API key returned)")
    cmd = "<show><config><running></running></config></show>"
    reply = requests.post(url, data={"type": "op", "cmd": cmd, "key": key}, verify=verify, timeout=120)
    reply.raise_for_status()
    root = ET.fromstring(reply.text)
    if root.get("status") != "success":
        raise RuntimeError(f"API error: {root.findtext('.//msg') or reply.text[:200]}")
    config = root.find(".//config")
    if config is None:
        raise RuntimeError("no <config> element in the reply")
    return ET.tostring(config, encoding="unicode")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--inventory", default="inventory.yml")
    parser.add_argument("--out", default="configs")
    parser.add_argument("--only", action="append", help="collect only this device (repeatable)")
    parser.add_argument("--insecure", action="store_true", help="skip TLS verification for API devices")
    args = parser.parse_args()

    devices = yaml.safe_load(Path(args.inventory).read_text())["devices"]
    if args.only:
        devices = [d for d in devices if d["name"] in args.only]
    if args.insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    user, password = credentials()

    failed = []
    for device in devices:
        name, platform = device["name"], device["platform"]
        try:
            if platform == "paloalto_panos":
                text, ext = collect_panos(device, user, password, verify=not args.insecure), "xml"
            elif platform in COMMANDS:
                text, ext = collect_cli(device, user, password), "cfg"
            else:
                raise RuntimeError(f"unknown platform {platform!r}; add it to COMMANDS")
        except Exception as exc:  # report every device, keep going
            failed.append(name)
            print(f"✗ {name}: {exc}")
            continue
        path = Path(args.out) / device.get("site", "default") / f"{name}.{ext}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(scrub(text).rstrip() + "\n", encoding="utf-8")
        print(f"✓ {name} -> {path}")

    print(f"{len(devices) - len(failed)} of {len(devices)} devices collected")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
