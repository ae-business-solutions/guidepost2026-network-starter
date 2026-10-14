# tests/test_ntp.py
# Every switch and router has at least two NTP servers, so logs line up during an incident.
#   good:  ntp server 192.0.2.123 / ntp server 192.0.2.124
#   bad:   one "ntp server" line, or none
from pathlib import Path


def test_two_ntp_servers():
    short = [
        f"{cfg.stem} ({count})"
        for cfg in Path("configs").rglob("*.cfg")
        if (count := cfg.read_text().count("\nntp server ")) < 2
    ]
    assert not short, short
