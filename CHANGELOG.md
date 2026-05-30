# Changelog

Format: [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

PRs touching roles, playbooks, or
[`docs/compliance-controls.yml`](./docs/compliance-controls.yml) must add
an `[Unreleased]` entry naming affected CTL- / POL- IDs.

## [Unreleased]

- 2026-05-30 remediation pass — runtime-correctness, security-baseline, and
  supply-chain hardening from the completed code audit. New ADRs:
  [ADR-002](docs/ADR-002-sre-toolchain-supply-chain.md) (supply-chain) and
  [ADR-003](docs/ADR-003-runtime-correctness-and-cis-baseline.md)
  (runtime-correctness + CIS baseline).
  - **Runtime defects fixed (no posture weakening):**
    - auditd restart handlers no longer use systemd (`auditd.service` ships
      `RefuseManualStop=yes`): rules reload via `augenrules --load`
      (no-op + reboot notice under immutability), config reloads via the
      SysV `service auditd restart` path; applied in both `auditd` and
      `log_forwarding`. CTL-002, CTL-003, POL-004, POL-005. (C1)
    - `playbooks/site-common.yml` runs `auditd` before `log_forwarding` so
      the audit package and `/etc/audit/plugins.d/` exist before the
      audisp-remote configs are written. CTL-002, CTL-003. (C2)
    - `sre_toolchain` dependency gate uses `which` instead of the shell
      builtin `command -v` under the `command` module. (C3)
    - fail2ban `[recidive]` pins `backend = auto` so it loads under the
      systemd backend. POL-002. (H1)
    - rsyslog TLS forwarding emits `$ActionSendStreamDriverPermittedPeer`
      via new `log_forwarding_tls_permitted_peer` (falls back to
      `x509/certvalid` when unset). POL-003. (H6)
    - `validate:` added to the chrony (`chronyd -p`) and fail2ban
      (`fail2ban-client -t`) config deploys. CTL-003, POL-002. (M5)
  - **Behaviour change — supply-chain (ADR-002):** `sre_toolchain`
    `checksum_policy` now defaults to **`strict`** (refuse unverified
    installs); adds optional keyless cosign signature verification
    (`sre_toolchain_verify_signatures` / `_require_signatures`) and optional
    per-tool tag pinning (`tag:`/`version:` in `vars/main.yml`); the
    evidence manifest now records resolved tag + SHA256 + verification
    outcomes; scratch dir always cleaned up. CTL-002, POL-002. `kubectx`
    (no upstream checksum) is now skipped by default. (H2, H3, M10)
  - **Behaviour change — account lockout (ADR-003):** `users` wires
    `pam_faillock` via `/usr/share/pam-configs/` profiles +
    `pam-auth-update` (idempotent, survives later `pam-auth-update` runs)
    instead of exact-string `pamd` edits, with a verification assertion and
    a documented lockout-recovery procedure. POL-001. (H4)
  - **Vault convention (H5):** encrypted secret files are named `vault.yml`
    (committed only encrypted), enforced by a new
    `scripts/check-vault-encrypted.sh` pre-commit guard; `.gitignore` and
    `CLAUDE.md` corrected; `vault_`-prefixed *variables* are the reviewer
    signal.
  - **CIS baseline extension (overridable, ADR-003):** sshd `MaxStartups`
    + variable `ListenAddress` (M1); sysctl `ip_forward`/forwarding/
    `secure_redirects` = 0 and `kexec_load_disabled`/`ldisc_autoload`/
    `perf_event_paranoid` (M2); auditd `execve` rules + `plugins.d` watch
    (M3); rkhunter `--propupd` gated to first install (M4); `TMOUT`+`umask`
    via `/etc/profile.d/99-hardening.sh` drop-in (M6). CTL-002, CTL-003,
    POL-001, POL-004.
  - **CI / tooling:** `requirements-dev.txt` pins installable
    `ansible-core==2.19.10` (the `2.21.0` pin did not exist on PyPI, breaking
    every CI job); all roles' `min_ansible_version` and README raised to
    `≥ 2.18` (community.general 13.x floor) (M9). `ci.yml` gains
    `concurrency`, per-job `timeout-minutes`, pip caching, and a `molecule`
    matrix job (M8). First Molecule scenario added for `users`
    (`roles/users/molecule/default/`) + `make molecule`/`molecule-deps`
    (M7, LIMITATIONS L2/L3/L5; **unrun here — no Docker**).
  - **Docs / evidence (N1, N2, L4, L7, L8):** `galaxy-sbom.py` adds a
    deterministic `serialNumber` (urn:uuid) and real tool version;
    `validate-compliance-controls.py` now enforces the **bidirectional**
    role↔CTL/POL header mapping (`sre_toolchain` added to CTL-002 and
    POL-002 `roles`); `common` locale no longer pins `LC_ALL`; `users`
    root-unlock-time difference documented; CTL-001 "MFA" wording softened
    (MFA delivered by the IdP, out of host-level scope). CTL-001, CTL-002,
    POL-002.
  - **Cross-repo:** `LICENSE` replaced with the canonical Apache-2.0 from
    `infra` (the prior copy was missing "reasonable and customary use in"
    from §6 Trademarks).
- CI supply-chain posture from the 2026-05-27 assurance engagement
  (Batch D); no role behaviour change, no
  `docs/compliance-controls.yml` change, no CTL- / POL- IDs touched.
  - `requirements-dev.txt` pins Python toolchain versions
    (`ansible-core`, `ansible-lint`, `yamllint`, `pre-commit`,
    `PyYAML`); all CI jobs and `make install` install from this single
    source. `.github/dependabot.yml` adds a `pip` ecosystem alongside
    the existing `github-actions` ecosystem so toolchain bumps are
    auto-tracked weekly (session finding B1).
  - `.github/workflows/ci.yml` pins all GitHub Actions to commit SHAs
    with `# vX.Y.Z` comments per OpenSSF Scorecard
    Pinned-Dependencies and SLSA v1.2 Source Track guidance.
    Dependabot reads the comment to identify newer commits
    (session finding B2).
  - `requirements.yml` pins Galaxy collections (`ansible.posix==2.2.0`,
    `community.general==13.0.1`) to exact versions instead of `>=`
    ranges. New `scripts/galaxy-sbom.py` reads
    `collections/ansible_collections/<ns>/<name>/MANIFEST.json` and
    emits a CycloneDX 1.6 SBOM; new `collections-sbom` CI job uploads
    the artifact with 90-day retention (`docs/ADR-001` F4.2). Scanning
    against a vulnerability feed deferred until tooling stabilises.
- Governance and tooling additions from the 2026-05-27 assurance
  engagement; no role behaviour change, no `docs/compliance-controls.yml`
  change, no CTL- / POL- IDs touched.
  - Root `CODE_OF_CONDUCT.md` adopting Contributor Covenant v2.1
    by reference (session finding B9).
  - Root `SECURITY.md` stub pointing at `.github/SECURITY.md` so
    external scanners that look at the repository root
    (OpenSSF Scorecard, supply-chain tools) find the security policy
    (B5).
  - `docs/policies/README.md`, `docs/controls/README.md`,
    `docs/evidence/README.md` navigation indexes for the POL- / CTL- /
    evidence views; `docs/compliance-controls.yml` remains canonical
    and is not duplicated (B4).
  - `CLAUDE.md` "Secrets management" section expanded with the vault
    password source convention (`ANSIBLE_VAULT_PASSWORD_FILE` preferred)
    and the `vault_` variable-aliasing pattern; new
    `inventories/development/group_vars/vault.yml.example` placeholder
    file (`LIMITATIONS.md` L4 and session finding B8).
  - `inventories/example/hosts` smoke-test fixture using RFC 6761
    `.example.test` hostnames; both playbooks now syntax-check without
    the "provided hosts list is empty" warning when targeted with
    `-i inventories/example/hosts` (`docs/ADR-001` F4.5).
  - `gitleaks` v8.30.1 pre-commit hook complementing the existing
    `detect-private-key` hook (B6).
  - `.github/ISSUE_TEMPLATE/bug_report.yml` `ansible-version`
    placeholder refreshed from `2.15` to `2.19` (B7).
  `make check` baseline: yamllint clean; ansible-lint production
  profile `0 failure(s), 0 warning(s) in 102 files processed of 142
  encountered`; `OK: 3 control(s), 5 policy(ies); roles
  cross-referenced against 11 role(s)`. Both playbooks syntax-check
  against `inventories/example/hosts` without warnings.
- Optimise and rewrite every `.md` file end-to-end for tighter prose,
  consistent voice, and uniform structure across the three companion
  repos: `README.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `LIMITATIONS.md`,
  `.github/SECURITY.md`, `.github/PULL_REQUEST_TEMPLATE.md`,
  `.github/copilot-instructions.md`, `docs/ADR-001-code-validation-baseline.md`,
  and all 11 `roles/<role>/README.md` files
  (`common`, `users`, `ntp`, `ssh_hardening`, `ufw`, `fail2ban`,
  `aide`, `rkhunter`, `log_forwarding`, `auditd`, `sre_toolchain`).
  ADR Status / Deciders / Findings / Decisions shape preserved; all
  factual content — defaults, variable descriptions, compliance
  mappings, F1–F4 finding categorisation, accepted design tensions
  F3.1–F3.6 — preserved verbatim. No role behaviour change, no
  playbook change, no `docs/compliance-controls.yml` change. No
  CTL-/POL- IDs touched. `make check` passes:
  `0 failure(s), 0 warning(s)`; `OK: 3 control(s), 5 policy(ies);
  roles cross-referenced against 11 role(s)`.
- Remove empty global `files/`, `templates/`, `host_vars/`, and
  `plugins/{filter,lookup,modules}/` stub directories — these are not part
  of the official Ansible best-practices layout (role-scoped `files/` /
  `templates/` are; top-level ones are not), were never populated, and
  would not be loaded without explicit `ansible.cfg` plugin paths. Per-env
  `inventories/<env>/group_vars/` and `inventories/<env>/host_vars/` are
  retained as documented extensibility points. `CLAUDE.md` and `README.md`
  Repository Structure sections updated to match. No role, playbook, or
  `docs/compliance-controls.yml` change; no CTL- / POL- IDs touched.
- Sync governance docs (SECURITY policy shape, PR template structure,
  copilot instructions, README Companion repositories pointer) with the
  companion `runbooks` and `infra` repos. No role, playbook, or
  `docs/compliance-controls.yml` change; no CTL- / POL- IDs touched.

## [0.0.0]

### Scaffolding (PR #18)

- Governance: `NOTICE`, `CHANGELOG.md`, `CONTRIBUTING.md`,
  `LIMITATIONS.md`, `.github/CODEOWNERS`, `.editorconfig`.
- `Makefile` (`help`, `install`, `lint`, `syntax-check`,
  `validate-compliance`, `check`, `molecule` placeholder, `clean`).
- `scripts/validate-compliance-controls.py` — structural check on
  `docs/compliance-controls.yml` + role cross-reference.
- `.pre-commit-config.yaml` running yamllint, ansible-lint (production
  profile), EditorConfig, hygiene.
- CI: `validate-compliance` and `pre-commit` jobs added.

### Initial Ansible structure

- 11 roles: `common`, `users`, `ntp`, `ssh_hardening`, `ufw`,
  `fail2ban`, `aide`, `rkhunter`, `log_forwarding`, `auditd`,
  `sre_toolchain`.
- `playbooks/site-common.yml` (fleet baseline) and
  `playbooks/sre-toolchain.yml` (operator hosts).
- 3-environment inventory scaffolding under `inventories/`.
- `docs/compliance-controls.yml` mapping CTL- / POL- IDs to NIS2 Art
  21–23, GDPR Art 5/25/32, ISO 27001 A.5–A.8, CRA Annex I, NISG 2026.
- ADR-001 — code-validation baseline (2026-05-24).
- CI: yamllint, ansible-lint (production profile), playbook syntax-check.
- `.github/SECURITY.md`, PR / issue templates, Dependabot.
