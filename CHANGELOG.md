# Changelog

Format: [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

PRs touching roles, playbooks, or
[`docs/compliance-controls.yml`](./docs/compliance-controls.yml) must add
an `[Unreleased]` entry naming affected CTL- / POL- IDs.

## [Unreleased]

- 2026-05-30 **New `apparmor` role — Mandatory Access Control / LSM (POL-001).**
  First of the defense-in-depth series. Ensures AppArmor (Ubuntu's default MAC)
  is installed (`apparmor` + `apparmor-utils`, plus the `apparmor-profiles` /
  `-profiles-extra` sets) and the service is active, **audits** profile
  coverage by parsing `aa-status --json` (enforce/complain/loaded counts), and
  **opt-in** moves named profiles into complain/enforce mode idempotently (only
  loaded profiles not already in the target mode are touched). Safe-by-default:
  `apparmor_enforce_profiles` / `_complain_profiles` are empty, so a baseline
  run only enables + audits and never flips a profile (which could break the
  confined program). Container-guest aware (`apparmor_runtime_managed`). Added
  to `site-common.yml` after `common` and mapped to POL-001 in
  `docs/compliance-controls.yml` (MAC = program-level information access
  restriction). CRA Annex I Part I, NIS2 Art 21.2(e), GDPR Art 25 / Art 5(1)(f),
  ISO 27001:2022 A.8.3 / A.5.15.

- 2026-05-30 **New `systemd_hardening` role — per-service sandboxing + audit
  (POL-004).** Confines services with systemd unit drop-ins
  (`/etc/systemd/system/<unit>.d/10-hardening.conf`) built from two vetted
  profiles (`local_daemon`, `network_daemon`: `NoNewPrivileges`,
  `ProtectSystem=strict`, `PrivateTmp`, `ProtectKernel*`,
  `RestrictAddressFamilies`, `SystemCallFilter=@system-service`,
  `CapabilityBoundingSet`, …), plus a read-only `systemd-analyze security`
  exposure audit (optional staging/CI threshold gate). **Safe-by-default:**
  `systemd_hardening_units` is empty, so a baseline run only audits and changes
  nothing until a unit is opted in; `systemd_hardening_restart_on_change` is
  `false`, so a changed drop-in is staged (daemon-reload) and activated on the
  unit's next restart rather than bouncing a live service. Container-guest
  aware (`systemd_hardening_runtime_managed`). Added to `site-common.yml` as
  the capstone role (runs last) and mapped to POL-004 in
  `docs/compliance-controls.yml`. CRA Annex I Part I, NIS2 Art 21.2(e),
  GDPR Art 25 / Art 5(1)(f), ISO 27001:2022 A.8.27.

- 2026-05-30 **New `wazuh_agent` role — HIDS/FIM endpoint (CTL-002, POL-002).**
  Installs and enrols the Wazuh agent (host intrusion detection, file integrity
  monitoring, rootcheck) against a Wazuh manager. Adds the Wazuh 4.x APT repo
  via a `signed-by` keyring (optional fingerprint pin verified when set);
  deploys `ossec.conf` (manager connection, authd auto-enrollment, syscheck on
  `/etc` realtime + `/usr/bin`/`/boot`/…, rootcheck, journald + auth/dpkg log
  collection); writes the enrollment password to `authd.pass` with `no_log`.
  **Off by default** (`wazuh_agent_enabled: false`); `site-common.yml` runs it
  only when enabled (requires `wazuh_manager_address`; the password is a vault
  var — public-repo-safe, no secret committed). Container-guest aware
  (`wazuh_runtime_managed`). Mapped to CTL-002 + POL-002. NIS2 Art 21.2(a)(b)
  + Art 23, GDPR Art 5(2), ISO 27001:2022 A.8.15/A.8.16.

- 2026-05-30 **New `dns` role — resolver hardening (POL-003).** Adds DNS
  handling via `systemd-resolved`: a `resolved.conf.d/90-ansible.conf` drop-in
  enabling DNSSEC (`allow-downgrade`), DNS-over-TLS (`opportunistic`), and
  disabling LLMNR/MulticastDNS, plus a local caching stub and the
  `/etc/resolv.conf` → stub symlink. Safe-by-default: `dns_resolvers` is empty,
  so link/DHCP (internal/split-horizon) DNS is preserved and only the
  hardening is layered on; public DoT resolvers are configured as *fallback*
  only. Container-guest aware (`dns_runtime_managed`): the service
  start/restart and resolv.conf symlink are skipped in container guests while
  the drop-in is still deployed. Added to `playbooks/site-common.yml` (after
  `ntp`) and mapped to POL-003 in `docs/compliance-controls.yml`. POL-003
  (DoT/DNSSEC), NIS2 Art 21.2(e), CRA Annex I, GDPR Art 32.

- 2026-05-30 **`auditd` container-awareness (CTL-002/003 — Molecule
  follow-up).** The `auditd` role now computes `auditd_runtime_managed`
  (honours the new `auditd_manage_runtime` default and requires a
  non-container `ansible_virtualization_type`) and gates the daemon
  start/enable plus the rule-load and config-reload handlers on it. The Linux
  audit subsystem is host-global and not namespaced, so in a container auditd
  cannot start and `auditctl`/`augenrules` fail (EPERM) — previously the
  daemon-start task aborted the converge, which kept the auditd Molecule leg
  red. `auditd.conf` and the rules file are still deployed (config-as-code),
  so the container verify still asserts them; real hosts are unaffected
  (their virt type is never a container, so the daemon is managed normally).
  Validated: ansible-lint 0/0, the gating expression across virt types
  (docker/lxc → skip; kvm/VMware/physical → manage), and the override. The
  full Molecule matrix stays on-demand (LIMITATIONS L2) until the remaining
  scenarios are confirmed on a Docker host.

- 2026-05-30 PR-review fixes (Copilot + Codex) on the dual-support /
  sysctl / vault / molecule work. No CTL-/POL- catalog membership changed
  (CTL-002, CTL-003, POL-004 cross-references touched in `common` /
  `sre_toolchain`).
  - **Molecule matrix is now on-demand (`workflow_dispatch`):** the
    `molecule` job runs systemd-in-Docker and exercises steps that are not
    container-safe (auditd rule loading, sshd restart, read-only sysctls), so
    it was never green and only added a perpetual red to PR CI. Gated it on
    `github.event_name == 'workflow_dispatch'` (removed `continue-on-error`),
    so push/PR CI no longer runs it; trigger it manually against a Docker host
    where converge is the real gate. Closure path (LIMITATIONS L2): add
    container-awareness to the affected roles, then re-enable on push/PR.
  - **`common` sysctl absence-robustness (Codex):** moved the absent-prone
    KSPP knobs `net.core.bpf_jit_harden` and `vm.unprivileged_userfaultfd`
    out of the unconditional `common_sysctl_settings` into the path-gated
    `common_sysctl_settings_optional` (they need `CONFIG_BPF_JIT` /
    `CONFIG_USERFAULTFD` and are commonly absent/namespaced in containers —
    the old placement failed the first sysctl loop where the `/proc` path is
    missing). Rewrote `tasks/sysctl.yml` to probe **every** key (both sets),
    write only present keys to `/etc/sysctl.d/90-ansible.conf`, and **remove
    any absent key from the drop-in before** the `reload: true` so a stale
    line can never break the whole-file `sysctl -p`. A host that loses a knob
    on a kernel change now re-converges cleanly without it. README + ADR-004 +
    `common` molecule verify updated (assert present knobs written, absent
    knobs NOT written). CTL-002, CTL-003, POL-004.
  - **`common` sysctl drop-in single-source prune (Codex follow-up):** the
    earlier cleanup only removed the role's own map keys that were absent on
    the kernel, so a key removed from the role *entirely* could leave a stale
    line (and `/etc/sysctl.d/90-ansible.conf` is shared with
    `kernel_hardening.yml`, so a blanket prune would wrongly delete its keys).
    Introduced `common_kernel_hardening_sysctl_keys` (defaults) as the single
    enumeration of the keys `kernel_hardening.yml` owns, and changed
    `tasks/sysctl.yml` to prune **every** drop-in key not in the union of the
    present map keys + those kernel-hardening keys — closing the
    removed-from-role stale-line case without fighting `kernel_hardening.yml`.
    Idempotent (nothing to prune on a stable host); kept the per-key
    `ansible.posix.sysctl` apply (no application-mechanism change). CTL-002,
    CTL-003, POL-004.
  - **Vault lint globs (Codex):** `.ansible-lint` `exclude_paths` now uses a
    `**/vault.yml` glob (matching `.yamllint`) so any documented vault path —
    including `inventories/<env>/host_vars/<host>/vault.yml` — is excluded,
    not just the three explicit `group_vars` files.
  - **Vault worked example moved out of the inventory load path (Codex):**
    relocated the encrypted example from
    `inventories/development/group_vars/vault.yml` to `docs/examples/vault.yml`
    (still ansible-vault encrypted, throwaway password `example`) so it no
    longer auto-loads — development inventory runs no longer require a vault
    password. The plaintext `vault.yml.example` template stays in the
    inventory. Updated the CI `vault-example` job path, CLAUDE.md, and
    LIMITATIONS L4; the `**/vault.yml` globs and `vault.yml` pre-commit guard
    still cover the new path. Re-verified it decrypts with `example`.
  - **`sre_toolchain` manifest idempotence (Codex):** the evidence manifest
    is now idempotent — the role reads the previous manifest, carries skipped
    tools' evidence forward unchanged, and reuses the prior `generated`
    timestamp when the substantive payload is identical, so a no-op converge
    rewrites byte-identical content and Molecule's idempotence step stays
    green. `make molecule-sre` keeps the full `molecule test` sequence.
    CTL-002.
  - **`sre_toolchain` molecule prepare (Codex):** added
    `molecule/default/prepare.yml` installing the role's required host
    commands (`jq`, `unzip`, `curl`, `tar`, `coreutils`, `ca-certificates`)
    into the clean geerlingguy containers before converge, so the run reaches
    the OPA/kubeconform download + checksum path instead of aborting on the
    up-front dependency check.
  - **Molecule kernel-scope wording (Codex):** `common` molecule comment,
    `common`/`sre_toolchain` READMEs, ADR-004, and LIMITATIONS L1 now state
    the dual-OS Docker legs share the host kernel and validate userspace/
    package behaviour across 24.04/26.04, NOT kernel-6.8-vs-7.0 sysctl
    differences (which need VM-backed runners). No kernel-7.0 sysctl proof is
    claimed from a container run.
  - **Makefile collection path (Copilot):** the `molecule` and `molecule-sre`
    targets `cd` into `roles/<role>`, so they now export
    `ANSIBLE_COLLECTIONS_PATH=$(CURDIR)/collections` (mirroring the CI fix) so
    local runs resolve `ansible.posix.*` / `community.general.*` from the
    repo-root `collections/` tree.

- 2026-05-30 Ubuntu 26.04 dual-support + residual-audit-gap closure. New ADR:
  [ADR-004](docs/ADR-004-ubuntu-2604-dual-support.md) (24.04 + 26.04
  dual-support; interim "CIS 24.04 + kernel-7.0/KSPP delta" benchmark
  stance). No CTL-/POL- catalog membership changed.
  - **Dual-OS support (ADR-004):** every role's `meta/main.yml` `platforms`
    block now declares `resolute` (26.04, kernel 7.0) alongside `noble`
    (24.04); meta descriptions and task headers updated to 24.04/26.04.
    README + CLAUDE.md "Target OS" now list both releases.
  - **Behaviour change — `common` sysctl baseline (kernel-7.0 / KSPP review,
    ADR-004):** added overridable always-present KSPP/CIS knobs to
    `common_sysctl_settings` (`fs.protected_fifos=2`,
    `fs.protected_regular=2`); added a **path-gated**
    `common_sysctl_settings_optional` dict applied only where the `/proc/sys`
    path exists (`net.core.bpf_jit_harden=2`, `vm.unprivileged_userfaultfd=0`,
    `kernel.io_uring_disabled=1`, `dev.tty.legacy_tiocsti=0`) so the baseline
    is idempotent across kernel 6.8 / 7.0 and on stripped containers (see the
    PR-review entry above — `bpf_jit_harden`/`unprivileged_userfaultfd` moved
    here from the unconditional set during review); made the
    previously-hardcoded `kernel_hardening.yml` sysctls overridable via
    `common_kernel_*` defaults (same values — no weakening).
    Re-validated `pam_faillock`/`pam-auth-update` and
    `unattended-upgrades`/`apt-listchanges` as unchanged on 26.04. CTL-002,
    CTL-003, POL-004.
  - **Molecule coverage (L2/L3/L5):** `users` scenario now tests **both**
    24.04 and 26.04 images; new converge+verify scenarios for
    `ssh_hardening` (sshd -t passes, weak KEX/ciphers absent),
    `auditd` (rules file + execve rule, no dead audisp watch), and `common`
    (new sysctls written to the drop-in), each dual-OS and added to the CI
    `molecule` matrix; new egress-gated `sre_toolchain` scenario
    (`opa`+`kubeconform`, manifest is valid JSON, strict-checksum path
    `verified`, signature path recorded `not_checked`) behind
    `make molecule-sre`. **All unrun here (no Docker; sre needs GitHub
    egress); CI `molecule` job stays `continue-on-error`.**
  - **Vault worked example (L4 closed):** shipped an *actually*
    ansible-vault-encrypted worked example at `docs/examples/vault.yml`
    (throwaway password `example`, placeholders only; relocated out of the
    inventory load path during review — see the PR-review entry above) so the
    `ansible-vault-encrypted` guard has a real file; new CI `vault-example`
    job decrypts it to prove the convention end-to-end; CLAUDE.md secrets
    section documents both the template and the encrypted example.
  - **Compliance-controls JSON Schema (L6 closed):** published
    `docs/schemas/compliance-controls.schema.json` (draft 2020-12),
    referenced from the YAML header; `validate-compliance-controls.py`
    validates against it when the optional `jsonschema` package is present
    (added to `requirements-dev.txt`) and keeps its structural checks
    authoritative otherwise.
  - **Docs:** LIMITATIONS L1 opened (dual-support), L2/L3/L5 expanded,
    L4/L6 closed; README ADR table + role READMEs updated.

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
