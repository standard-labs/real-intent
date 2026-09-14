#!/usr/bin/env python3
"""Reject GitHub-hosted compute in repository workflows."""

from pathlib import Path
import re


workflow_dir = Path(__file__).resolve().parents[1] / ".github" / "workflows"
workflows = sorted((*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")))
if not workflows:
    raise SystemExit("no workflows found")

for workflow in workflows:
    source = workflow.read_text(encoding="utf-8")
    runners = re.findall(r"^\s*runs-on:\s*(.+?)\s*$", source, flags=re.MULTILINE)
    if not runners:
        raise SystemExit(f"{workflow}: no runs-on declarations found")
    for runner in runners:
        if not runner.startswith("[self-hosted, netcup,"):
            raise SystemExit(f"{workflow}: disallowed runner {runner}")

print(f"validated {len(workflows)} Vienna-only workflow(s)")
