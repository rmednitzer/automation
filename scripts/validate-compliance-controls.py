#!/usr/bin/env python3
"""Validate ``docs/compliance-controls.yml`` structure and role cross-references.

Run from the repository root::

    python3 scripts/validate-compliance-controls.py

Exits ``0`` if the file conforms to the project convention (see
``CLAUDE.md`` and the file's header comment). Exits ``1`` on any
violation, printing the failing rule and the offending entry.

The check is intentionally minimal — it enforces the structural rules that
the project relies on for audit and PR review, without prescribing a formal
JSON Schema (see ``LIMITATIONS.md`` L6).

Rules enforced:

1. The top-level document is a mapping with optional ``controls`` and
   ``policies`` keys (at least one of them must be non-empty).
2. Each control ID matches ``CTL-NNN``; each policy ID matches ``POL-NNN``
   (three digits).
3. Controls require fields: ``title``, ``description``,
   ``regulatory_mapping``, ``roles``.
4. Policies require fields: ``title``, ``description``,
   ``regulatory_mapping``.
5. ``regulatory_mapping`` is a non-empty list of strings of the form
   "Framework Article — description" (hyphen or em dash accepted).
6. Every role referenced under a control's ``roles`` list exists as a
   directory under ``roles/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTROLS_FILE = REPO_ROOT / "docs" / "compliance-controls.yml"
ROLES_DIR = REPO_ROOT / "roles"

REQUIRED_CONTROL_FIELDS = ("title", "description", "regulatory_mapping", "roles")
REQUIRED_POLICY_FIELDS = ("title", "description", "regulatory_mapping")
CONTROL_ID_PREFIX = "CTL-"
POLICY_ID_PREFIX = "POL-"


def fail(msg: str) -> None:
    """Print *msg* to stderr and exit 1."""
    print(f"compliance-validate: {msg}", file=sys.stderr)
    sys.exit(1)


def discover_role_names() -> set[str]:
    if not ROLES_DIR.is_dir():
        fail(f"roles directory not found: {ROLES_DIR}")
    return {p.name for p in ROLES_DIR.iterdir() if p.is_dir()}


def validate_id(entry_id: str, prefix: str, kind: str) -> None:
    if not entry_id.startswith(prefix):
        fail(f"{kind} id '{entry_id}' must start with '{prefix}'")
    suffix = entry_id[len(prefix):]
    if not (suffix.isdigit() and len(suffix) == 3):
        fail(f"{kind} id '{entry_id}' must be {prefix}NNN with three digits")


def validate_regulatory_mapping(entry_id: str, mapping: object) -> None:
    if not isinstance(mapping, list) or not mapping:
        fail(f"{entry_id}: regulatory_mapping must be a non-empty list")
    for ref in mapping:
        if not isinstance(ref, str):
            fail(f"{entry_id}: regulatory_mapping entries must be strings; "
                 f"got {type(ref).__name__}")
        # Accept hyphen or em dash as a separator.
        if "—" not in ref and " - " not in ref and "- " not in ref:
            fail(
                f"{entry_id}: regulatory_mapping entry "
                f"'{ref}' should follow 'Framework Article — description'"
            )


def validate_controls(controls: dict, known_roles: set[str]) -> None:
    for cid, body in controls.items():
        validate_id(cid, CONTROL_ID_PREFIX, "control")
        if not isinstance(body, dict):
            fail(f"{cid}: must be a mapping")
        for field in REQUIRED_CONTROL_FIELDS:
            if field not in body:
                fail(f"{cid}: missing required field '{field}'")
        validate_regulatory_mapping(cid, body["regulatory_mapping"])
        roles = body["roles"]
        if not isinstance(roles, list) or not roles:
            fail(f"{cid}: 'roles' must be a non-empty list")
        for role in roles:
            if not isinstance(role, str):
                fail(f"{cid}: role entry '{role!r}' must be a string")
            if role not in known_roles:
                fail(
                    f"{cid}: references role '{role}', but no directory "
                    f"'roles/{role}/' exists"
                )


def validate_policies(policies: dict) -> None:
    for pid, body in policies.items():
        validate_id(pid, POLICY_ID_PREFIX, "policy")
        if not isinstance(body, dict):
            fail(f"{pid}: must be a mapping")
        for field in REQUIRED_POLICY_FIELDS:
            if field not in body:
                fail(f"{pid}: missing required field '{field}'")
        validate_regulatory_mapping(pid, body["regulatory_mapping"])


def main() -> None:
    if not CONTROLS_FILE.exists():
        fail(f"controls file not found: {CONTROLS_FILE}")

    with CONTROLS_FILE.open("r", encoding="utf-8") as fh:
        try:
            data = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            fail(f"YAML parse error: {exc}")

    if not isinstance(data, dict):
        fail("top-level document must be a mapping")

    controls = data.get("controls") or {}
    policies = data.get("policies") or {}

    if not controls and not policies:
        fail("at least one of 'controls' or 'policies' must be non-empty")

    known_roles = discover_role_names()

    validate_controls(controls, known_roles)
    validate_policies(policies)

    print(
        f"OK: {len(controls)} control(s), {len(policies)} policy(ies); "
        f"roles cross-referenced against {len(known_roles)} role(s)."
    )


if __name__ == "__main__":
    main()
