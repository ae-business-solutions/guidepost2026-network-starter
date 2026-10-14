# tests/test_firewall_tickets.py
# Every Palo Alto security rule names its ServiceNow change ticket in the description.
#   good:  <description>CHG0012345 web tier to app tier</description>
#   bad:   no description, or no CHG number
# Rules that predate the policy go in tests/known_rules.txt, one rule name per line.
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

TICKET = re.compile(r"\bCHG\d{7}\b")


def test_rules_have_change_tickets():
    configs = list(Path("configs").rglob("*.xml"))
    if not configs:
        pytest.skip("no PAN-OS configs in configs/")
    known = Path("tests/known_rules.txt")
    exempt = set(known.read_text().split("\n")) if known.exists() else set()
    missing = [
        f"{cfg.stem} {rule.get('name')}"
        for cfg in configs
        for rule in ET.parse(cfg).iterfind(".//security/rules/entry")
        if rule.get("name") not in exempt and not TICKET.search(rule.findtext("description") or "")
    ]
    assert not missing, missing
