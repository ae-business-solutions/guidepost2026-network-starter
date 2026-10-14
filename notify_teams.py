"""Post failed network unit tests to a Microsoft Teams channel.

    pytest tests --junitxml=results.xml || python notify_teams.py results.xml

The URL comes from TEAMS_WEBHOOK_URL: create it in Teams with the Workflows template
"Post to a channel when a webhook request is received". Treat the URL as a secret.
Standard library only.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET


def failures(junit_file: str) -> list[str]:
    lines = []
    for case in ET.parse(junit_file).iter("testcase"):
        problem = case.find("failure")
        if problem is None:
            problem = case.find("error")
        if problem is not None:
            reason = (problem.get("message") or "").splitlines()[0][:300]
            lines.append(f"**{case.get('name')}**: {reason}")
    return lines


def card(title: str, lines: list[str]) -> dict:
    body = [{"type": "TextBlock", "text": title, "weight": "Bolder", "size": "Medium", "wrap": True}]
    body += [{"type": "TextBlock", "text": line, "wrap": True} for line in lines[:20]]
    if len(lines) > 20:
        body.append({"type": "TextBlock", "text": f"... and {len(lines) - 20} more", "wrap": True})
    run = os.environ.get("GITHUB_RUN_ID")
    if run:
        url = f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{run}"
        body.append({"type": "TextBlock", "text": f"[Open the run]({url})", "wrap": True})
    content = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": body,
    }
    return {
        "type": "message",
        "attachments": [{"contentType": "application/vnd.microsoft.card.adaptive", "content": content}],
    }


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    lines = failures(argv[0])
    if not lines:
        print("no failures; nothing to post")
        return 0
    url = os.environ.get("TEAMS_WEBHOOK_URL")
    message = card(f"Network unit tests: {len(lines)} failing", lines)
    if not url:
        print("TEAMS_WEBHOOK_URL is not set; this is what would be posted:")
        print(json.dumps(message, indent=2))
        return 0
    request = urllib.request.Request(
        url, data=json.dumps(message).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=30) as reply:
        print(f"posted to Teams ({reply.status})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
