# tests/test_bpduguard.py
# Every access port has BPDU guard, so a looped or rogue switch can't take down the VLAN.
#   good:  interface Ethernet3 / switchport access vlan 10 / spanning-tree bpduguard enable
#   bad:   interface Ethernet3 / switchport access vlan 10
from pathlib import Path


def test_access_ports_have_bpduguard():
    missing = []
    for cfg in Path("configs").rglob("*.cfg"):
        for intf in cfg.read_text().split("\ninterface ")[1:]:
            name, _, body = intf.partition("\n")
            body = body.split("\n!")[0]
            if "access vlan" in body and "bpduguard" not in body:
                missing.append(f"{cfg.stem} {name}")
    assert not missing, missing
