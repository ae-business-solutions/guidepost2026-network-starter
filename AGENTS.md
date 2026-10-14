# AGENTS.md: network-starter

Small Python tools for steps 1–5 of the talk. Keep them small: one file per tool, standard library plus `requests`, `pyyaml` and `netmiko`.

## Commands

```bash
pip install -r requirements.txt
pytest tests -q                          # network unit tests on configs/
python scrub.py --check configs          # must report nothing
```

## Rules

- Everything here is read-only against devices. Never add a command that enters configuration mode or changes a device; step 5's change is made by a person or by a separate, reviewed tool.
- Credentials come only from `NET_USERNAME` / `NET_PASSWORD` or a prompt. Never write them to disk, logs or URLs.
- Everything written to `configs/` goes through `scrub.py` first.
- A new network unit test is one file in `tests/`, under 30 lines, with a good and a bad example in its header comment. It reads `configs/` only.
- Prompts in `prompts/` keep the same headings: Overview, Tools, Inputs or Topology, Output, Architecture.
