#!/usr/bin/env python3
"""Advisory AI compliance review for a pull request, using LOCAL inference.

AI-in-CI (capability #7). Reviews the PR's changed Ansible role compliance
headers against the control catalog (docs/compliance-controls.yml) using a
*local* Ollama inference endpoint, so code and compliance data never leave the
estate for a third-party model API (POL-004 / ADR-006 — the same data-
sovereignty rationale as the `ollama` role).

It is deliberately ADVISORY and NON-BLOCKING: any problem (no endpoint
configured, endpoint unreachable, empty/garbled response) results in a graceful
skip and ``exit 0``. CI is never gated on model output — the deterministic
``validate-compliance-controls.py`` remains the authoritative gate. Findings are
written to the GitHub step summary.

Configuration (environment):
  OLLAMA_ENDPOINT     base URL of the local inference endpoint (required to run)
  OLLAMA_MODEL        model tag (default: llama3.1:8b)
  BASE_SHA            base commit to diff against (default: origin/main)
  AI_REVIEW_TIMEOUT   request timeout seconds (default: 120)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

ENDPOINT = os.environ.get("OLLAMA_ENDPOINT", "").rstrip("/")
MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
BASE = os.environ.get("BASE_SHA", "") or "origin/main"
TIMEOUT = int(os.environ.get("AI_REVIEW_TIMEOUT", "120"))
SUMMARY = os.environ.get("GITHUB_STEP_SUMMARY", "")
HEADER = "### AI compliance review (advisory — local inference)"


def emit(markdown: str) -> None:
    """Write to the GitHub step summary (if present) and stdout."""
    if SUMMARY:
        with open(SUMMARY, "a", encoding="utf-8") as handle:
            handle.write(markdown + "\n")
    print(markdown)


def skip(reason: str) -> "None":
    emit(f"{HEADER}\n\n_Skipped: {reason}. Advisory only — does not gate merge._")
    sys.exit(0)


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False
    )
    return result.stdout


def main() -> None:
    if not ENDPOINT:
        skip("no local inference endpoint configured (set the AI_REVIEW_OLLAMA_ENDPOINT variable)")

    changed = [
        line
        for line in git("diff", "--name-only", f"{BASE}...HEAD").splitlines()
        if line.startswith(("roles/", "playbooks/")) or line == "docs/compliance-controls.yml"
    ]
    headers = [f for f in changed if f.endswith("defaults/main.yml")]
    if not headers:
        skip("no role compliance headers changed")

    context_blocks = []
    for path in headers:
        try:
            with open(path, encoding="utf-8") as handle:
                head = "".join(handle.readlines()[:45])
        except OSError:
            continue
        context_blocks.append(f"#### {path}\n{head}")

    try:
        with open("docs/compliance-controls.yml", encoding="utf-8") as handle:
            catalog = handle.read()
    except OSError:
        catalog = ""

    prompt = (
        "You are a compliance reviewer for an Ansible fleet-hardening repository. "
        "The control catalog defines CTL-/POL- controls and lists which roles "
        "implement each. For the CHANGED role compliance headers below, flag ONLY "
        "concrete issues: (1) a header that cites a CTL-/POL- id while that role is "
        "not listed under that control in the catalog (or the reverse); (2) a "
        "missing compliance header; (3) a compliance/hardening claim that looks "
        "unsupported. Be concise, use bullet points, and reply exactly "
        "'No issues found.' if there are none.\n\n"
        f"# Changed role headers\n{''.join(context_blocks)}\n\n"
        f"# Control catalog (truncated)\n{catalog[:8000]}\n"
    )

    payload = json.dumps(
        {"model": MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0}}
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{ENDPOINT}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            body = json.loads(response.read())
        review = (body.get("response") or "").strip()
    except (urllib.error.URLError, OSError, ValueError, TimeoutError) as exc:
        skip(f"local inference endpoint unavailable ({exc.__class__.__name__})")

    if not review:
        skip("empty model response")

    emit(
        f"{HEADER}\n\n"
        f"_Model `{MODEL}` via local inference; {len(headers)} changed role header(s)._\n\n"
        f"{review}\n\n---\n"
        "_Advisory only — does not gate merge; the deterministic "
        "`validate-compliance-controls.py` is authoritative. See docs/ADR-006._"
    )


if __name__ == "__main__":
    main()
