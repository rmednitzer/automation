#!/usr/bin/env python3
"""Export the fleet's compliance posture as a machine-readable JSON artifact.

This is the fleet -> AI-layer bridge (see docs/ADR-007): it turns the
authoritative, human-maintained sources —

  - ``docs/compliance-controls.yml`` (controls/policies, their regulatory
    mappings, and the roles that implement each), and
  - ``playbooks/site-common.yml`` (which roles are in the fleet baseline) —

into one self-describing JSON document the MCP gateway can serve, so the AI
layer can answer questions like "which controls apply to the fleet", "what
implements POL-001", or "what does CTL-002 map to in NIS2/GDPR" without parsing
Ansible itself. It is READ-ONLY and emits to stdout (or ``--output FILE``).

The output is deterministic — sorted, no embedded timestamp — so it is
reproducible and diffable in CI (the server adds its own served-at). The
deterministic ``validate-compliance-controls.py`` remains the source of truth
for catalog/role consistency; this script only reshapes already-valid data.

Run from the repository root::

    python3 scripts/export-compliance-posture.py            # -> stdout
    python3 scripts/export-compliance-posture.py -o posture.json

Exits 0 on success, 1 on a read/parse error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTROLS_FILE = REPO_ROOT / "docs" / "compliance-controls.yml"
BASELINE_PLAYBOOK = REPO_ROOT / "playbooks" / "site-common.yml"
SCHEMA = "fleet-compliance-posture/v1"

# Regulatory frameworks recognised in regulatory_mapping strings (see CLAUDE.md).
KNOWN_FRAMEWORKS = (
    "NIS2",
    "NISG",
    "CRA",
    "GDPR",
    "DSG",
    "ISO/IEC 27001",
    "ISO 27001",
    "NIST",
    "BSI",
)


def die(msg: str) -> None:
    print(f"export-compliance-posture: {msg}", file=sys.stderr)
    sys.exit(1)


def load_yaml(path: Path) -> object:
    try:
        with path.open(encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exc:
        die(f"cannot read {path}: {exc}")
        return None  # unreachable (die exits); keeps type-checkers happy


def baseline_roles() -> dict[str, bool]:
    """Map each role used by site-common.yml to whether it is conditional
    (gated by ``when:``). Roles absent here are not in the fleet baseline."""
    plays = load_yaml(BASELINE_PLAYBOOK)
    result: dict[str, bool] = {}
    if not isinstance(plays, list):
        return result
    for play in plays:
        if not isinstance(play, dict):
            continue
        for entry in play.get("roles", []) or []:
            if isinstance(entry, str):
                result[entry] = False
            elif isinstance(entry, dict) and "role" in entry:
                result[str(entry["role"])] = "when" in entry
    return result


def frameworks_in(mapping: list) -> list[str]:
    found = []
    for ref in mapping:
        for name in KNOWN_FRAMEWORKS:
            if name in ref and name not in found:
                found.append(name)
    return found


def build_entries(catalog: dict, key: str) -> list[dict]:
    """Return a sorted list of control/policy entries from the catalog."""
    section = catalog.get(key) or {}
    entries = []
    for entry_id in sorted(section):
        body = section[entry_id] or {}
        entries.append(
            {
                "id": entry_id,
                "title": body.get("title", "").strip(),
                "description": " ".join((body.get("description") or "").split()),
                "regulatory_mapping": list(body.get("regulatory_mapping") or []),
                "roles": sorted(body.get("roles") or []),
            }
        )
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the fleet compliance posture as JSON.")
    parser.add_argument("-o", "--output", help="write JSON here instead of stdout")
    args = parser.parse_args()

    catalog = load_yaml(CONTROLS_FILE)
    if not isinstance(catalog, dict):
        die(f"{CONTROLS_FILE} did not parse as a mapping")

    controls = build_entries(catalog, "controls")
    policies = build_entries(catalog, "policies")
    in_baseline = baseline_roles()

    # Invert the catalog: each role -> the control/policy ids that implement it,
    # plus whether it is in the baseline and (if so) gated by a condition.
    implements: dict[str, list[str]] = {}
    for entry in controls + policies:
        for role in entry["roles"]:
            implements.setdefault(role, []).append(entry["id"])

    roles = [
        {
            "name": name,
            "implements": sorted(implements[name]),
            "in_baseline": name in in_baseline,
            "conditional": in_baseline.get(name, False),
        }
        for name in sorted(implements)
    ]

    framework_tally: dict[str, int] = {}
    for entry in controls + policies:
        for name in frameworks_in(entry["regulatory_mapping"]):
            framework_tally[name] = framework_tally.get(name, 0) + 1

    posture = {
        "schema": SCHEMA,
        "source": {
            "catalog": str(CONTROLS_FILE.relative_to(REPO_ROOT)),
            "baseline_playbook": str(BASELINE_PLAYBOOK.relative_to(REPO_ROOT)),
        },
        "summary": {
            "controls": len(controls),
            "policies": len(policies),
            "roles": len(roles),
            "baseline_roles": sum(1 for r in roles if r["in_baseline"]),
            "frameworks": len(framework_tally),
        },
        "frameworks": dict(sorted(framework_tally.items())),
        "controls": controls,
        "policies": policies,
        "roles": roles,
    }

    text = json.dumps(posture, indent=2, sort_keys=False, ensure_ascii=False) + "\n"
    if args.output:
        try:
            Path(args.output).write_text(text, encoding="utf-8")
        except OSError as exc:
            die(f"cannot write {args.output}: {exc}")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
