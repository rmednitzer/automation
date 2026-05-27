#!/usr/bin/env python3
"""Generate a CycloneDX 1.6 SBOM for the installed Ansible Galaxy collections.

Reads ``MANIFEST.json`` files under
``collections/ansible_collections/<namespace>/<name>/`` (the layout that
``ansible-galaxy install -r requirements.yml`` produces in this repo's
configured ``collections_path``) and emits a CycloneDX 1.6 SBOM to stdout.

Closes ADR-001 F4.2. Galaxy lacks a first-class advisory feed today; this
SBOM is the supply-chain evidence step (what the resolved set looks like
at apply time). Scanning happens in a follow-up once a feed or scanner
is identified.

The PURL type ``pkg:galaxy/...`` follows the proposed Galaxy purl type
under discussion at the package-url/purl-spec project. It is not yet
ratified; consumers that strictly validate purl types should pre-process.
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COLLECTIONS_ROOT = REPO_ROOT / "collections" / "ansible_collections"


def discover_components() -> list[dict]:
    """Return one CycloneDX component dict per installed collection."""
    components: list[dict] = []
    for manifest_path in sorted(COLLECTIONS_ROOT.glob("*/*/MANIFEST.json")):
        with manifest_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        info = data.get("collection_info", {})
        namespace = info.get("namespace")
        name = info.get("name")
        if not namespace or not name:
            continue
        version = info.get("version", "0.0.0")
        fqcn = f"{namespace}.{name}"

        component: dict = {
            "type": "library",
            "name": fqcn,
            "version": version,
            "purl": f"pkg:galaxy/{namespace}/{name}@{version}",
        }

        external_refs: list[dict] = []
        repository = info.get("repository")
        if repository:
            external_refs.append({"type": "vcs", "url": repository})
        homepage = info.get("homepage")
        if homepage and homepage != repository:
            external_refs.append({"type": "website", "url": homepage})
        issues = info.get("issues")
        if issues:
            external_refs.append({"type": "issue-tracker", "url": issues})
        if external_refs:
            component["externalReferences"] = external_refs

        licence = info.get("license")
        if licence:
            licences = licence if isinstance(licence, list) else [licence]
            component["licenses"] = [{"license": {"id": lid}} for lid in licences]

        components.append(component)

    return components


def build_sbom(components: list[dict]) -> dict:
    """Wrap the components in a CycloneDX 1.6 envelope."""
    timestamp = (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "metadata": {
            "timestamp": timestamp,
            "tools": [
                {
                    "vendor": "automation",
                    "name": "galaxy-sbom.py",
                    "version": "1",
                }
            ],
            "component": {
                "type": "application",
                "name": "automation",
            },
        },
        "components": components,
    }


def main() -> int:
    if not COLLECTIONS_ROOT.is_dir():
        print(
            "galaxy-sbom: no collections installed; "
            "run `ansible-galaxy install -r requirements.yml` first",
            file=sys.stderr,
        )
        return 1

    components = discover_components()
    if not components:
        print("galaxy-sbom: no MANIFEST.json files found", file=sys.stderr)
        return 1

    sbom = build_sbom(components)
    json.dump(sbom, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
