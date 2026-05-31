#!/usr/bin/env python3
"""Validate ``docs/compliance-controls.yml`` structure and role cross-references.

Run from the repository root::

    python3 scripts/validate-compliance-controls.py

Exits ``0`` if the file conforms to the project convention (see
``CLAUDE.md`` and the file's header comment). Exits ``1`` on any
violation, printing the failing rule and the offending entry.

The check enforces the structural rules that the project relies on for audit
and PR review. A formal JSON Schema (draft 2020-12) is also published at
``docs/schemas/compliance-controls.schema.json`` (closing ``LIMITATIONS.md``
L6); this script validates against it when the optional ``jsonschema``
package is installed, and otherwise leaves the structural rules below
authoritative (the project stays dependency-light — PyYAML only).

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
7. Reverse cross-reference (bidirectional). For every CTL-/POL- id and
   every role:
     a. if ``compliance-controls.yml`` lists a role under an id, that
        role's ``defaults/main.yml`` compliance header must cite the id;
     b. if a role's ``defaults/main.yml`` header cites a CTL-/POL- id, the
        matching control/policy must list that role under ``roles`` (and
        the id must exist).
   This stops ``docs/compliance-controls.yml`` and the role headers from
   silently drifting apart (see CLAUDE.md and ADR-001 finding F1.11).
8. The document validates against the published JSON Schema at
   ``docs/schemas/compliance-controls.schema.json`` (only when ``jsonschema``
   is installed; the schema file must always be valid JSON).
9. Framework coverage. Every framework the repository declares alignment with
   (``EXPECTED_FRAMEWORKS``, mirroring the file header and the README
   "Regulatory Scope") is cited by at least one ``regulatory_mapping`` entry,
   so a declared-but-unmapped framework (the gap that left CRA Annex I and
   NISG 2026 unmapped) cannot ship silently.
10. Derived-index parity. ``docs/controls/README.md`` and
    ``docs/policies/README.md`` are convenience views that mirror the YAML's
    role coverage; each CTL-/POL- row's role set must equal the canonical set,
    so the indexes cannot drift (they had fallen 11 roles behind before this).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTROLS_FILE = REPO_ROOT / "docs" / "compliance-controls.yml"
SCHEMA_FILE = REPO_ROOT / "docs" / "schemas" / "compliance-controls.schema.json"
ROLES_DIR = REPO_ROOT / "roles"

REQUIRED_CONTROL_FIELDS = ("title", "description", "regulatory_mapping", "roles")
REQUIRED_POLICY_FIELDS = ("title", "description", "regulatory_mapping")
CONTROL_ID_PREFIX = "CTL-"
POLICY_ID_PREFIX = "POL-"

# Matches CTL-NNN / POL-NNN identifiers in a role's defaults header comments.
COMPLIANCE_ID_RE = re.compile(r"\b(?:CTL|POL)-\d{3}\b")

# Frameworks the repository declares alignment with (the compliance-controls.yml
# header and the README "Regulatory Scope"). Each MUST be cited by at least one
# regulatory_mapping entry, or the declared scope is aspirational rather than
# implemented. The key is the citation prefix used in regulatory_mapping entries
# ("NIS2 Art …", "CRA Annex I …", "NISG 2026 — …", etc.); keep it in sync with
# the file header and README when the scope genuinely changes.
EXPECTED_FRAMEWORKS = {
    "NIS2": "NIS2 Directive (EU 2022/2555)",
    "NISG 2026": "NISG 2026 (Austrian NIS2 transposition)",
    "CRA": "Cyber Resilience Act (EU 2024/2847) Annex I",
    "GDPR": "GDPR (EU 2016/679) / Austrian DSG",
    "ISO 27001": "ISO/IEC 27001:2022",
}

# Derived, human-facing navigation indexes that MIRROR the role coverage in
# compliance-controls.yml. They are convenience views (each says so), so they
# drift silently when a role is added — rule 10 keeps their per-id role lists in
# lockstep with the canonical YAML. Map of id prefix -> file.
DERIVED_INDEX_FILES = {
    "CTL": REPO_ROOT / "docs" / "controls" / "README.md",
    "POL": REPO_ROOT / "docs" / "policies" / "README.md",
}

# A derived-index table row: | CTL-001 | <title> | `role`, `role`, … |
DERIVED_INDEX_ROW_RE = re.compile(r"^\|\s*((?:CTL|POL)-\d{3})\s*\|[^|]*\|\s*(.*?)\s*\|")


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


def parse_role_header_ids() -> dict[str, set[str]]:
    """Map each role to the CTL-/POL- ids cited in its defaults header.

    Reads ``roles/<role>/defaults/main.yml`` as text and extracts every
    ``CTL-NNN`` / ``POL-NNN`` token (the compliance header is a comment
    block, so we scan the raw file rather than the parsed YAML). Roles
    without a ``defaults/main.yml`` contribute an empty set.
    """
    role_ids: dict[str, set[str]] = {}
    for role_dir in sorted(p for p in ROLES_DIR.iterdir() if p.is_dir()):
        defaults = role_dir / "defaults" / "main.yml"
        ids: set[str] = set()
        if defaults.is_file():
            text = defaults.read_text(encoding="utf-8")
            ids = set(COMPLIANCE_ID_RE.findall(text))
        role_ids[role_dir.name] = ids
    return role_ids


def validate_reverse_mapping(
    controls: dict, policies: dict, role_header_ids: dict[str, set[str]]
) -> None:
    """Enforce bidirectional role <-> CTL/POL consistency (rule 7)."""
    # Forward: id -> set(roles) declared in compliance-controls.yml.
    declared: dict[str, set[str]] = {}
    for eid, body in {**controls, **policies}.items():
        roles = body.get("roles") or []
        declared[eid] = {r for r in roles if isinstance(r, str)}

    # 7a: every declared (id, role) pair must be cited in the role header.
    for eid, roles in declared.items():
        for role in roles:
            header = role_header_ids.get(role, set())
            if eid not in header:
                fail(
                    f"reverse-map: {eid} lists role '{role}', but "
                    f"roles/{role}/defaults/main.yml compliance header does "
                    f"not cite {eid} (add it, or remove the role from {eid})"
                )

    # 7b: every id cited in a role header must be declared for that role.
    for role, ids in role_header_ids.items():
        for eid in sorted(ids):
            if eid not in declared:
                fail(
                    f"reverse-map: roles/{role}/defaults/main.yml cites "
                    f"{eid}, but no such control/policy exists in "
                    f"docs/compliance-controls.yml"
                )
            if role not in declared[eid]:
                fail(
                    f"reverse-map: roles/{role}/defaults/main.yml cites "
                    f"{eid}, but {eid}'s 'roles' list omits '{role}' "
                    f"(add it, or drop the header reference)"
                )


def validate_framework_coverage(controls: dict, policies: dict) -> None:
    """Rule 9: every declared framework is cited by >= 1 regulatory_mapping.

    Guards against a framework being named in scope (the file header and the
    README "Regulatory Scope") while no control or policy actually maps to it —
    the exact gap this check was added to close, where CRA Annex I and NISG 2026
    were declared frameworks but every regulatory_mapping cited only NIS2 / GDPR
    / ISO 27001. A declared-but-unmapped framework is aspirational, not
    implemented, and must not ship silently.
    """
    refs: list[str] = []
    for body in {**controls, **policies}.values():
        mapping = body.get("regulatory_mapping") or []
        refs.extend(ref for ref in mapping if isinstance(ref, str))
    for key, label in EXPECTED_FRAMEWORKS.items():
        if not any(ref.startswith(key) for ref in refs):
            fail(
                f"framework-coverage: '{key}' ({label}) is declared in scope "
                f"but no regulatory_mapping entry cites it — add a mapping that "
                f"starts with '{key}', or remove it from the declared frameworks"
            )


def validate_derived_indexes(controls: dict, policies: dict) -> None:
    """Rule 10: docs/{controls,policies}/README.md role tables mirror the YAML.

    These indexes are convenience views that duplicate each control/policy's
    role coverage, so they drift silently when a role is added (they had fallen
    11 roles behind before this check existed). Every CTL-/POL- row's role set
    must equal the canonical compliance-controls.yml role set. A missing index
    file is fine (it is optional); a present row that disagrees fails the build.
    """
    combined = {**controls, **policies}
    for _prefix, path in DERIVED_INDEX_FILES.items():
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            match = DERIVED_INDEX_ROW_RE.match(line)
            if not match:
                continue
            eid, roles_cell = match.group(1), match.group(2)
            if eid not in combined:
                fail(
                    f"derived-index: {path.relative_to(REPO_ROOT)} lists {eid}, "
                    f"which does not exist in compliance-controls.yml"
                )
            doc_roles = set(re.findall(r"`([a-z0-9_]+)`", roles_cell))
            yaml_roles = {
                r for r in (combined[eid].get("roles") or []) if isinstance(r, str)
            }
            if doc_roles != yaml_roles:
                missing = sorted(yaml_roles - doc_roles)
                extra = sorted(doc_roles - yaml_roles)
                detail = "; ".join(
                    part
                    for part in (
                        f"missing {missing}" if missing else "",
                        f"unexpected {extra}" if extra else "",
                    )
                    if part
                )
                fail(
                    f"derived-index: {path.relative_to(REPO_ROOT)} row {eid} role "
                    f"list is out of sync with compliance-controls.yml ({detail})"
                )


def validate_against_schema(data: object) -> str:
    """Validate *data* against the published JSON Schema (L6).

    The schema at ``docs/schemas/compliance-controls.schema.json`` (draft
    2020-12) is the formal contract for the file's structure. We validate
    against it only when the optional ``jsonschema`` package is installed —
    the project stays dependency-light (PyYAML only), so when ``jsonschema``
    is absent the structural checks above remain authoritative and the
    schema stands as published documentation. Returns a short status string
    for the summary line; calls :func:`fail` on a schema violation.
    """
    if not SCHEMA_FILE.exists():
        fail(f"schema file not found: {SCHEMA_FILE}")

    # The schema must always be loadable as JSON, even without jsonschema,
    # so a malformed schema is caught in CI rather than shipping silently.
    import json

    try:
        schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"schema is not valid JSON: {exc}")

    try:
        import jsonschema
    except ImportError:
        return "schema present (jsonschema not installed — structural check authoritative)"

    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as exc:
        location = "/".join(str(p) for p in exc.absolute_path) or "<root>"
        fail(f"schema validation failed at '{location}': {exc.message}")
    except jsonschema.SchemaError as exc:
        fail(f"the JSON Schema itself is invalid: {exc.message}")
    return "schema validated (jsonschema)"


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

    role_header_ids = parse_role_header_ids()
    validate_reverse_mapping(controls, policies, role_header_ids)

    validate_framework_coverage(controls, policies)
    validate_derived_indexes(controls, policies)

    schema_status = validate_against_schema(data)

    print(
        f"OK: {len(controls)} control(s), {len(policies)} policy(ies); "
        f"roles cross-referenced against {len(known_roles)} role(s); "
        f"bidirectional header cross-references consistent; "
        f"all {len(EXPECTED_FRAMEWORKS)} declared frameworks mapped; "
        f"derived indexes in sync; "
        f"{schema_status}."
    )


if __name__ == "__main__":
    main()
