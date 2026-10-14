# Prompts

Copy a prompt into your AI coding tool, fill in the `<placeholders>`, and let it build. Each one follows the same shape: Overview, Tools, Inputs or Topology, Output, Architecture.

| Step | Prompt | What you get |
| --- | --- | --- |
| 1 | [1-firewall-rulebase-explorer.md](1-firewall-rulebase-explorer.md) | A script that pulls a PAN-OS rulebase and writes an HTML audit report |
| 1 | [1-config-explorer.md](1-config-explorer.md) | A script that turns a folder of switch configs into an HTML explorer with an Issues view |
| 2 | [2-containerlab-lab.md](2-containerlab-lab.md) | A leaf-spine Containerlab lab that works on first boot |
| 2 | [2-cloud-lab.md](2-cloud-lab.md) | A Terraform Azure Virtual WAN lab (or AWS Transit Gateway) you can destroy when done |
| 3 | [3-extend-collection.md](3-extend-collection.md) | `collect.py` support for another platform |
| 4 | [4-new-unit-test.md](4-new-unit-test.md) | A new offline unit test in `tests/` |
| 5 | [5-upgrade.md](5-upgrade.md) | An HA-pair upgrade wrapped in a before-and-after state diff |

## The safe pattern

Ask the AI to write a tool that runs on your machine. The tool reads the configs; the AI only sees your prompt. When you do paste configs into a chat, run `python scrub.py` on them first.

Read what it writes, run it yourself, and keep it in git.
