# Overview
Pull the security policy from a Palo Alto Networks VM-Series firewall and produce a single-page HTML report for exploring and auditing the rulebase.

# Tools
- Python 3 with `requests`
- PAN-OS XML API, read-only calls only
- Any UI approach you like, but the output must be one self-contained HTML file: no CDNs, no external calls
- Make it look good

# Inputs
- Firewall address and username as arguments
- Prompt for the password; never save credentials or the API key
- `--insecure` flag for self-signed certificates (verify by default)

# Output
One HTML file, named `rulebase-<hostname>-<date>.html`, with:
- **Rules**: every security rule in order, searchable, sortable and filterable by zone, source, destination, application, service and action. Address and service objects and groups resolve in place.
- **Issues**: findings with a severity and a one-line reason:
  - any/any rules (source, destination, application or service)
  - shadowed or redundant rules
  - disabled rules
  - rules with no description, or no change ticket (e.g. `CHG1234567`) in the description
  - rules without log-at-session-end, or without a security profile group
  - unused rules, if hit counts are available
- **Cleanup list**: rules to remove or tighten, with the reason, downloadable as CSV

# Architecture
- One script: connect, pull, write the HTML file, exit
- No commits and no configuration changes
- Clear errors for bad credentials, unreachable firewall or API errors
- The firewall's config stays on my machine; only this prompt goes to the AI
