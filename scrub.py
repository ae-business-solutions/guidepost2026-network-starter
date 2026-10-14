"""Mask secrets in device configs before they go into git or an AI chat.

    python scrub.py FILE_OR_FOLDER [...]     # rewrites the files in place
    python scrub.py --check FILE_OR_FOLDER   # lists what it would mask, changes nothing

Masks the rest of the line after: secret, password, key, key-string, community,
auth (SNMPv3), passphrase and *-secret / *-password / *-key (CLI configs); the same
names as XML elements (PAN-OS and other XML exports); and whole PEM blocks.
It errs toward masking too much. Review the result before sharing it anyway.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

MASK = "<removed>"
XML_MASK = "&lt;removed&gt;"  # the same text, escaped so the XML stays valid
WORDS = r"secret|password|passwd|key|key-string|community|auth|passphrase|phash|authpwd|privpwd"

# CLI: the keyword, then the rest of the line (encryption type and value). `key chain NAME` is left alone.
CLI = re.compile(rf"(?i)(?<![\w-])((?:[\w-]*-)?(?:{WORDS}))(\s+)(?!{re.escape(MASK)}|chain\b)\S.*$", re.MULTILINE)
# XML: <password>...</password>, <phash>...</phash>, <key>...</key> and friends.
XML = re.compile(rf"(?i)<((?:[\w-]*-)?(?:{WORDS}))>[^<]+</\1>")
PEM = re.compile(r"-----BEGIN [A-Z ]+-----.*?-----END [A-Z ]+-----", re.DOTALL)


def scrub(text: str) -> str:
    if text.lstrip().startswith("<"):
        text = PEM.sub(f"-----{XML_MASK}-----", text)
        return XML.sub(rf"<\1>{XML_MASK}</\1>", text)
    text = PEM.sub(f"-----{MASK}-----", text)
    return CLI.sub(rf"\1\2{MASK}", text)


def _files(paths: list[str]) -> list[Path]:
    found: list[Path] = []
    for raw in paths:
        path = Path(raw)
        found += sorted(p for p in path.rglob("*") if p.is_file()) if path.is_dir() else [path]
    return found


def main(argv: list[str]) -> int:
    check = "--check" in argv
    paths = [a for a in argv if a != "--check"]
    if not paths:
        print(__doc__)
        return 2
    for path in _files(paths):
        before = path.read_text(encoding="utf-8", errors="replace")
        after = scrub(before)
        if before == after:
            continue
        changed = sum(1 for a, b in zip(before.splitlines(), after.splitlines(), strict=False) if a != b)
        print(f"{path}: {changed} line(s) {'would be ' if check else ''}masked")
        if not check:
            path.write_text(after, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
