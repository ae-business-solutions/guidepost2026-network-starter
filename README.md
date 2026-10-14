# guidepost2026-network-starter

Five low-risk ways to start automating your network with AI, from the talk "Network Automation in the AI Era". Steps 1–4 never write to a device. Step 5 is the first that does.

| Step | What | Risk | Here |
| --- | --- | --- | --- |
| 1 | Turn configs into an HTML explorer with an Issues view; audit a firewall rulebase | None: offline copies | [`prompts/1-*`](prompts/) |
| 2 | Build a lab from one prompt: Containerlab or a cloud network with Terraform | None to production | [`prompts/2-*`](prompts/), [`lab/`](lab/) |
| 3 | Back up configs into git on a schedule, with a read-only account | Low: read-only | [`collect.py`](collect.py), [`inventory.yml`](inventory.yml) |
| 4 | Network unit tests on those backups; failures go to Teams | None: offline copies | [`tests/`](tests/), [`notify_teams.py`](notify_teams.py) |
| 5 | Capture switch state before and after a change, and diff it | Medium: you make the change | [`statediff.py`](statediff.py), [`prompts/5-upgrade.md`](prompts/5-upgrade.md) |

Step 6, a source of truth that drives config, is in the four `guidepost2026-network-*` repos.

## Before you use AI on network data

1. Use your company's approved AI tool, on a plan that doesn't train on your data
2. Scrub secrets first: `python scrub.py <file or folder>` (or build your own)
3. Work on copies: exported configs and labs, not live devices
4. Ask for self-contained output: one HTML file with no external scripts or network calls
5. Read what it writes, run it yourself, and keep it in git

## Set up

```bash
git clone https://github.com/ae-business-solutions/guidepost2026-network-starter
cd guidepost2026-network-starter
python -m venv .venv && . .venv/bin/activate    # Python 3.10+. Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Step 1: configs into an app

Copy [`prompts/1-config-explorer.md`](prompts/1-config-explorer.md) or [`prompts/1-firewall-rulebase-explorer.md`](prompts/1-firewall-rulebase-explorer.md) into your AI coding tool. It writes a script; you run it on your machine. The configs never go to the AI.

## Step 2: a lab

The lab in [`lab/`](lab/) is two Arista cEOS switches and a Linux host, enough for steps 3–5. It needs Linux with Docker, [Containerlab](https://containerlab.dev) and the cEOS image (free Arista account; never push it to a public registry).

```bash
sudo containerlab deploy -t lab/starter.clab.yml
sudo containerlab destroy -t lab/starter.clab.yml --cleanup    # when done
```

For a bigger lab or a cloud lab, start from [`prompts/2-containerlab-lab.md`](prompts/2-containerlab-lab.md) or [`prompts/2-cloud-lab.md`](prompts/2-cloud-lab.md).

## Step 3: config backups

```bash
export NET_USERNAME=collector NET_PASSWORD=collector    # the lab's read-only user
python collect.py
git add configs && git commit -m "Config backup"
```

[`inventory.yml`](inventory.yml) lists the devices. Any Netmiko platform works over SSH, and Palo Alto firewalls work over the XML API. Every config goes through `scrub.py` before it's saved.

To run it nightly, add `NET_USERNAME` and `NET_PASSWORD` as repo secrets, give a self-hosted runner the label `netops` (it needs to reach your devices), and uncomment the schedule in [`.github/workflows/collect.yml`](.github/workflows/collect.yml).

## Step 4: network unit tests

```bash
pytest tests -q
```

Each test is one short file that reads `configs/`:

| Test | Checks |
| --- | --- |
| [`test_bpduguard.py`](tests/test_bpduguard.py) | Every access port has BPDU guard |
| [`test_ntp.py`](tests/test_ntp.py) | Every device has at least two NTP servers |
| [`test_firewall_tickets.py`](tests/test_firewall_tickets.py) | Every PAN-OS security rule has a `CHG` ticket in its description |

Try it: on sw1 in the lab, remove `spanning-tree bpduguard enable` from Ethernet3, run `collect.py`, then `pytest`. The test names the port.

The [`network-tests`](.github/workflows/tests.yml) workflow runs them after every collection and on every push. Add a `TEAMS_WEBHOOK_URL` secret (Teams → channel → Workflows → "Post to a channel when a webhook request is received") and failures post to that channel. Write your next test with [`prompts/4-new-unit-test.md`](prompts/4-new-unit-test.md).

## Step 5: before-and-after state

```bash
python statediff.py capture 172.20.20.11 before.json --insecure
# ... make the change: an upgrade, a reboot, a config change ...
python statediff.py capture 172.20.20.11 after.json --insecure
python statediff.py diff before.json after.json
```

It captures version, interfaces up, BGP peers, LLDP neighbors, routes, ARP and MAC counts, MLAG and memory over eAPI, then prints a verdict and exits 1 if anything needs a look. Here is a leaf after an upgrade where one spine uplink didn't come back:

```text
dc1-leaf1a                  before     after
Version                    4.32.3M   4.34.2F  changed
Interfaces up                   56        55  CHECK: Ethernet50/1
BGP peers established            3         2  CHECK: default/10.255.255.2
LLDP neighbors                   5         4  CHECK: Ethernet50/1 -> dc1-spine2
Routes                       1,204     1,202
ARP entries                    312       309
MAC entries                  1,876     1,861
MLAG                        active    active
Memory used %                   41        44

Verdict: HOLD, 3 thing(s) to look at.
```

To see a HOLD in the lab, run `shutdown` on sw1's Ethernet2 (as `admin`) between the two captures and wait ten seconds. It's Arista EOS only; to build a full upgrade for your platform around it, use [`prompts/5-upgrade.md`](prompts/5-upgrade.md).

## Working with AI coding tools

[`AGENTS.md`](AGENTS.md) gives any coding agent this repo's rules; `CLAUDE.md` imports it.

## License

Apache-2.0
