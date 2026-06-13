# Phase 2/3 — Security and quality findings register (`automation`)

Audit pass: `audit/2026-06-13-full-pass`. Schema: ID, title, severity, location,
evidence, exploit-plausibility, disposition. Severity: critical / high / medium
/ low / info.

## Summary

`automation` is a mature, compliance-aligned hardening repo. The full gate suite
is green (see `01-baseline.md`). A line-level review of the Python/shell scripts,
both CI workflows, and the 22 roles found **no critical or high findings and no
active vulnerabilities**. The findings below are all **defense-in-depth: defaults
that could be stronger**, where the secure *mechanism already exists and works*
and the open posture is a deliberate, documented opt-in. None is fixed inline —
each is either an intentional design choice that should not be silently
overridden, or an untestable change in this environment (no Docker/Molecule).
All are tracked in `BACKLOG.md`.

## Coverage (this session)

| Area | Method | Result |
|------|--------|--------|
| Python scripts | Manual review (`yaml.safe_load`, no `shell=True`, no `eval/exec`) | clean (one info item, A-I1) |
| `check-vault-encrypted.sh` | Manual review | clean |
| `ai-compliance-review.yml` | Workflow review (trigger, permissions, interpolation) | clean (see A-I1) |
| `ci.yml` | Workflow review | clean (SHA-pinned, least-priv, no `pull_request_target`) |
| 22 roles | Spot + targeted review (downloads, become, modes, TLS, creds) | findings A-1..A-5 below |
| Secrets | gitleaks history (49 commits) + tracked tree | 0 |

## Findings (all deferred to BACKLOG.md)

### A-1 — Wazuh APT key fingerprint pin unset by default
- Severity: low (defense-in-depth)
- Location: `roles/wazuh_agent/defaults/main.yml` (`wazuh_apt_key_fingerprint: ""`)
- Evidence: the role fetches the key over HTTPS into a scoped `signed-by`
  keyring (`/usr/share/keyrings/wazuh.asc` -> dearmored keyring), and **enforces
  a fingerprint pin when one is set** (`tasks/main.yml:47-70`, fail-closed
  assertion before the key is trusted). The default empty value means the
  optional pin is simply not asserted; it is **not** "verification disabled".
- Exploit-plausibility: low — requires a compromised CDN/MITM of an HTTPS
  endpoint AND the operator not setting the (supported) pin. `wazuh_agent` is
  opt-in (needs a manager endpoint).
- Disposition: backlog A-1. Ship the published Wazuh GPG fingerprint as the
  default (verified against an authoritative source), or document the pin as a
  required hardening step. Not changed inline: the empty default is a deliberate
  "optional pin" design (code comment), and hardcoding a fingerprint risks
  breaking installs on key rotation if not paired with a rotation process.

### A-2 — Vector/Datadog APT key fingerprint pin unset by default
- Severity: low (defense-in-depth)
- Location: `roles/vector/defaults/main.yml` (`vector_apt_key_fingerprints: []`)
- Evidence: identical pattern to A-1 — keys are built into a **staging** keyring
  and the pin is asserted on staging *before* the keyring goes live
  (`tasks/main.yml:75-88`). Default empty = optional pin not asserted.
- Disposition: backlog A-2 (folds with A-1). `vector` is opt-in (needs a sink).

### A-3 — sre_toolchain cosign certificate-identity regexp is broad by default
- Severity: low (only when signatures opted into)
- Location: `roles/sre_toolchain/defaults/main.yml:55`
  (`...identity_regexp: "^https://github.com/.+/.github/workflows/.+@.+"`)
- Evidence: when `sre_toolchain_verify_signatures: true` (default **false**,
  line 40), this accepts a binary signed by *any* GitHub Actions workflow in
  *any* repo, weakening the provenance guarantee to "signed by some GH Actions
  run". The always-on SHA256 checksum check (`checksum_policy: strict` default,
  line 31) is unaffected, so this is not a checksum bypass.
- Exploit-plausibility: low — needs the operator to enable cosign verification
  AND an attacker able to land a cosign-signed artifact from an unrelated repo
  matching the broad identity. The strict checksum still gates the bytes.
- Disposition: backlog A-3. Narrow to per-tool identity regexps (e.g.
  `^https://github.com/cli/cli/\.github/workflows/`). M-effort (per-tool
  research) with regression risk if a regexp is wrong; not a safe inline edit.

### A-4 — kubectx/kubens unverified under non-default `best-effort` checksum policy
- Severity: low (non-default path)
- Location: `roles/sre_toolchain/tasks/install_kubectx.yml`
- Evidence: kubectx/kubens publish no upstream checksum file; the **strict**
  default skips them (correct, fail-closed). Only `checksum_policy: best-effort`
  installs them unverified.
- Disposition: backlog A-4. When `verify_signatures: true`, verify via the
  cosign-attested release digest; otherwise keep strict's skip.

### A-5 — Ollama temp archive written world-readable (`0644`) in `/tmp`
- Severity: low (nit)
- Location: `roles/ollama/tasks/main.yml:104`
- Evidence: the download IS checksum-verified (`checksum: "{{ ollama_checksum }}"`,
  line 101); only the temp `.tgz` mode is `0644` (root-owned, removed after
  extract). `sre_toolchain` uses a `0700` scratch dir — inconsistent.
- Disposition: backlog A-5. Use `0600` (or a `0700` scratch dir). Not changed
  inline: `ollama` has no Molecule scenario and Docker is unavailable here, so
  the change can't be test-covered this session (mission rule: no untested
  behavior change).

### A-I1 — AI-in-CI step-summary rendering (info, by design)
- Severity: info
- Location: `scripts/ai-compliance-review.py:144`; `ai-compliance-review.yml`
- Evidence: the LLM response is written to `GITHUB_STEP_SUMMARY` unsanitized.
  The workflow uses `pull_request` (not `pull_request_target`),
  `permissions: contents: read`, fetches its script from `BASE_SHA` (trusted
  ref, not the PR branch), and does not interpolate PR title/body into shell.
  The model is LOCAL (ADR-006/POL-004). Exploitable only by someone who can
  influence the local model output.
- Disposition: accepted design; noted for awareness. No change.

## Reviewed — confirmed clean (no action)

Scripts (`validate-compliance-controls.py`, `export-compliance-posture.py`,
`galaxy-sbom.py`): `yaml.safe_load`, no subprocess, no eval/exec.
`ai-compliance-review.py`: subprocess list-form, local-only endpoint.
`ci.yml`: digest-pinned actions, least privilege, no `pull_request_target`.
`ssh_hardening`: `PermitRootLogin no`, password auth off, `sshd -t` pre-deploy.
`users`: passwordless sudo off, root locked, yescrypt, pam_faillock on.
`redfish`: `validate_certs: true`, `no_log` on creds, power changes hard-gated.
`wazuh_agent` creds: `authd.pass` `0640 root:wazuh`, `no_log`.
All 22 roles: no `validate_certs: false`, no hardcoded creds, no `curl | bash`,
no global `become: true`.

## Secrets

gitleaks: 0 leaks over 49 commits of history and the tracked tree. The 130
`--no-git` hits are entirely under the gitignored, CI-absent `collections/`
(third-party fixtures); excluded by `.gitleaks.toml`. No stop conditions
encountered.
