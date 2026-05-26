# ADR-001: Code validation baseline

- **Status:** Accepted
- **Date:** 2026-05-24
- **Deciders:** automation maintainers
- **Supersedes:** none
- **Related commits:**
  - `bc890aa` (2026-05-16) — Full code audit: runtime defects, unsafe
    defaults, metadata drift
  - `8635dc1` (2026-05-15) — License standardisation on Apache-2.0
  - `37f00b0` (2026-05-13) — CTL/POL identifier digit standardisation
  - `577f799` (2026-05-12) — CTL/POL reference harmonisation across role
    headers

## Context

`automation` provides the technical-control surface for an EU/Austrian
compliance posture (NIS2 / NISG 2026 / CRA / GDPR / ISO 27001:2022).
Each role is mapped to controls (`CTL-001..CTL-003`) and policies
(`POL-001..POL-005`) defined in
[`docs/compliance-controls.yml`](compliance-controls.yml), which in
turn cite the regulatory articles they discharge.

For an artifact in that role, "the lint passes" is necessary but not
sufficient: a misconfigured `auditd` rule set, a stale `sshd_config`
template, or a doc that contradicts the shipping default can all pass
static analysis while quietly weakening the posture an auditor will be
shown. We therefore commit to a periodic full-tree validation pass
whose findings, scope, and resulting decisions are recorded under
`docs/ADR-*.md`.

This ADR captures the 2026-05-24 baseline validation: what was indexed,
what was checked against known-good sources, what was found, and what
the project commits to as a result.

## Decision drivers

- Static lint cleanliness alone has historically masked real runtime
  defects (see `bc890aa`: dead audit forwarding, inert `pam_faillock`,
  duplicate logrotate stanzas, etc.).
- Doc/code drift accumulates faster than the compliance narrative can
  absorb — an auditor reading `roles/<name>/README.md` must see the
  same defaults the playbook actually applies.
- The repository is the source-of-truth for technical evidence;
  inconsistencies between `CLAUDE.md`, `README.md`, role docs, and
  shipping templates create the appearance of uncontrolled change
  (against POL-005).

## Scope

- 10 roles: `common`, `users`, `ntp`, `ssh_hardening`, `ufw`,
  `fail2ban`, `aide`, `rkhunter`, `log_forwarding`, `auditd`
- 18 Jinja2 templates
- 10 handler files
- 5 inventory directories (3 environments, `group_vars/`, `host_vars/`)
- Top-level configuration: `ansible.cfg`, `requirements.yml`,
  `.ansible-lint`, `.yamllint`, `.gitignore`,
  `.github/workflows/ci.yml`, `.github/dependabot.yml`,
  `.github/SECURITY.md`, `.github/PULL_REQUEST_TEMPLATE.md`,
  `.github/copilot-instructions.md`, three issue templates
- `group_vars/all.yml` and `playbooks/site-common.yml`
- `docs/compliance-controls.yml`
- `CLAUDE.md`, `README.md`, `LICENSE`

## Methodology

1. **Code index** — every YAML, Jinja2, and Markdown file under the
   repository root read end-to-end and cross-tabulated against the
   role/template/handler matrix.
2. **Static analysis** — `yamllint` (default rules + project overrides)
   and `ansible-lint` (profile `production`, FQCN enforced,
   `no-changed-when` enforced) executed against the working tree after
   `ansible-galaxy install -r requirements.yml`. Playbook
   `--syntax-check` run on `playbooks/*.yml`.
3. **Validation against known-good sources** — role behaviour and
   template content compared against:
   - CIS Ubuntu Linux Benchmark (auditd rule keys; password policy;
     filesystem mount options; `/etc/login.defs` keys; sysctl baseline)
   - BSI TR-02102-4 (SSH KEX / cipher / MAC selection)
   - OpenSSH `sshd_config(5)` manual (option syntax and acceptable
     values for Ubuntu 24.04 LTS openssh-server)
   - `chrony.conf(5)`, `chrony` documentation (directive syntax, NTS)
   - Ubuntu 24.04 audit framework layout
     (`/etc/audit/plugins.d/` replaces `/etc/audisp/plugins.d/`)
   - `pam_faillock(8)` / `pam_pwquality(8)` documentation (stack
     placement; `faillock.conf` keys; `pwquality.conf` keys)
   - UFW and Fail2Ban upstream documentation (jail/action semantics)
   - AIDE and rkhunter upstream configuration references
   - Ansible best-practices: FQCN usage, become discipline,
     handler/notify pattern, `changed_when`/`failed_when` on
     command/shell tasks, `validate:` on config templates
4. **Doc parity check** — every key variable advertised in each
   `roles/<name>/README.md` reconciled against
   `roles/<name>/defaults/main.yml`.
5. **Compliance traceability** — `roles/<name>/defaults/main.yml`
   compliance headers checked against the role list in each
   control/policy in `docs/compliance-controls.yml`.

## Findings

### F1 — Validated (no remediation required)

- **F1.1 FQCN coverage: 100 %.** All task modules use
  `ansible.builtin.*`, `ansible.posix.*`, or `community.general.*`.
  `.ansible-lint` enforces this via the `fqcn` rule in the production
  profile; CI is the gate.
- **F1.2 Privilege escalation discipline.** `ansible.cfg` sets
  `become = false` globally; every privileged task sets `become: true`
  explicitly. No blanket `become` in playbooks.
- **F1.3 Linter clean.** `yamllint` and `ansible-lint` (production
  profile) both pass on the working tree: `0 failure(s), 0 warning(s)`.
- **F1.4 Syntax clean.** `ansible-playbook --syntax-check` passes for
  `playbooks/site-common.yml`.
- **F1.5 SSH crypto selection** is BSI TR-02102-4 / Mozilla-modern
  aligned: no SHA-1 MACs, no CBC ciphers, no legacy DH groups,
  Ed25519 preferred. Weak `/etc/ssh/moduli` lines (< 3071 bits) are
  pruned by `roles/ssh_hardening/tasks/main.yml`.
- **F1.6 Audit framework path** uses Ubuntu 24.04's
  `/etc/audit/plugins.d/` for audisp plugins; the 2.x
  `/etc/audisp/plugins.d/` regression noted in `bc890aa` is fixed and
  verified.
- **F1.7 PAM faillock wiring.** `community.general.pamd` adds
  `pam_faillock` preauth/authfail/authsucc to `common-auth` and the
  account hook to `common-account`, so `faillock.conf` is actually
  enforced (POL-001).
- **F1.8 Logrotate de-duplication.** The role replaces
  `/etc/logrotate.d/rsyslog` in place rather than dropping in
  compliance-* overlays, avoiding the "duplicate log entry" abort that
  historically silenced all rotation.
- **F1.9 Idempotent destructive helpers.** `ssh moduli` filter,
  world-writable-directory sticky-bit pass, and `ufw raw_rules` carry
  `changed_when` predicates that match real state changes.
- **F1.10 No secrets in tree.** No private keys, SSH authorized_keys,
  passwords, mailto values, certificate material, or SIEM endpoints
  are populated; all sensitive values are empty defaults that the
  inventory operator must supply.
- **F1.11 Compliance traceability.** Every role listed under a control
  or policy in `docs/compliance-controls.yml` has a corresponding
  compliance header block in `roles/<name>/defaults/main.yml`.
- **F1.12 Role count and playbook ordering.** `playbooks/site-common.yml`
  applies all 10 roles in the order required for safety: SSH hardened
  before UFW; NTP before audit so timestamps are correct; auditd last
  to capture every preceding mutation.

### F2 — Documentation drift (remediated in this change)

Cases where the shipping default was correct but the role README still
described the **pre-`bc890aa`** value, or where new variables landed
without README coverage.

| File | README said | Actual default |
|------|-------------|----------------|
| `roles/users/README.md` | `users_password_min_length: 12` | `14` |
| `roles/users/README.md` | `users_sudo_require_tty: true` | `false` |
| `roles/users/README.md` | `users_lock_root: false` | `true` |
| `roles/ssh_hardening/README.md` | `ssh_permit_root_login: prohibit-password` | `"no"` |
| `roles/fail2ban/README.md` | `fail2ban_bantime: 1h` | `6h` |
| `roles/rkhunter/README.md` | `rkhunter_apt_hook: true` | `false` |
| `roles/rkhunter/README.md` ("does") | APT hook listed as a feature | Default off; rationale documented |
| `roles/auditd/README.md` | `auditd_buffer_size: 8192` | `16384` |
| `roles/auditd/README.md` | `auditd_max_log_file: 50` | `100` |
| `roles/auditd/README.md` | `auditd_num_logs: 10` | `20` |
| `roles/common/README.md` | No coverage of kernel-module blacklist, `/tmp`/`/var/tmp` mount hardening, core-dump disable, log-retention tiers | Variables present in defaults |
| `roles/log_forwarding/README.md` | No coverage of `log_forwarding_audit_port` / `log_forwarding_audit_transport` | Variables present in defaults |
| `roles/ntp/README.md` | No coverage of `ntp_nts_enabled` / `ntp_nts_servers` | Variables present in defaults |
| `CLAUDE.md` (line 31) | `LICENSE  # GNU General Public License v3` | Apache License 2.0 |

All corrected in the same commit that adds this ADR.

### F3 — Accepted design tensions (no change)

Real coupling points where the cheap automation fix would introduce a
worse failure mode than the current manual coordination. Recorded so
the trade-off is explicit when revisited.

- **F3.1 `ssh_port` cross-role coupling.** `ssh_port` is consumed only
  by `ssh_hardening`. `ufw_rules` and the fail2ban `sshd` jail must be
  updated by hand when it changes. Auto-deriving UFW/fail2ban rules
  from `ssh_port` would create a single point of regression — a typo
  would simultaneously break the firewall and the SSH banaction. Matches
  the warning comment in `group_vars/all.yml`.
- **F3.2 `auditd_immutable = true` by default.** `-e 2` blocks live
  rule reloads until reboot. Required for CIS posture; the
  `Restart auditd` handler cannot live-load rule changes. Operators
  tuning rules frequently must set `auditd_immutable: false` in
  inventory.
- **F3.3 `rkhunter_apt_hook = false` by default.** Auto-`propupd` after
  every dpkg invocation silently re-baselines the integrity database —
  defeating the detection it claims to provide. Opt in explicitly to
  enable.
- **F3.4 `common_harden_tmp_remount = false` by default.** Live remount
  of `/tmp` discards open file handles and wipes existing content on a
  running host. The fstab entry is always written; the hardened options
  take effect on next boot. Set true only on fresh hosts where an
  immediate remount is safe.
- **F3.5 `log_forwarding_server` defaults to `""`.** With no SIEM
  endpoint declared, both the rsyslog forwarding rule and the
  audisp-remote destination are skipped. Intentional so un-configured
  hosts do not ship logs to an invalid address; the deploy is a no-op
  rather than a noisy failure.
- **F3.6 No role-to-role meta dependencies.** Sequencing is encoded in
  `playbooks/site-common.yml` rather than in `meta/main.yml`
  `dependencies:`. Keeps each role re-usable in isolation and avoids
  hidden invocations, at the cost of relying on playbook ordering for
  correctness.

### F4 — Opportunities (out of scope for this ADR)

Tracked here for traceability; none block the current posture.
Implementation will require a separate ADR and design pass.

- **F4.1 Molecule scenarios** per role. CI currently runs lint plus
  `--syntax-check`. Idempotency, converge, verify, and side-effect
  tests would catch regressions like the `bc890aa` class earlier.
- **F4.2 Galaxy collection supply-chain scanning** in CI (dependabot
  covers GitHub Actions only).
- **F4.3 SBOM generation** for the managed-host package set (CRA Annex
  II).
- **F4.4 `validate:` hooks on more templates.** `sshd_config` and
  `sudoers.d/99-ansible-hardening` validate before apply. The same
  pattern fits `chrony.conf` (`chronyd -p`), `jail.local`
  (`fail2ban-client -t`), and `audit.rules.j2` (`auditctl -R` against
  a copy).
- **F4.5 Inventory regression.** `--syntax-check` warns "provided
  hosts list is empty" because the three inventory `hosts` files only
  contain commented-out examples. Acceptable for a template repository
  but worth a smoke-test fixture (e.g. `inventories/example/`) so the
  syntax check runs against a populated tree.

## Decisions

1. **Doc parity is a release criterion.** Any change to a
   `roles/<name>/defaults/main.yml` that touches a variable documented
   in the role's README must update the README in the same commit. The
   PR template's checklist reflects this.
2. **ADRs live under `docs/ADR-NNN-<slug>.md`** with sequential
   numbering. Status, deciders, related commits, and a Findings
   section are required.
3. **`Apache-2.0` is the project license** and the only license
   identifier permitted in role `meta/main.yml`, `README.md`,
   `CLAUDE.md`, and any new documentation.
4. **`docs/compliance-controls.yml` is canonical** for control and
   policy identifiers. Role headers and READMEs reference these IDs by
   literal name; renumbering requires an ADR.
5. **Findings F3.1 – F3.6 are documented constraints, not bugs.**
   Reverting any of them requires an ADR that supersedes the relevant
   subsection of this one.

## Consequences

- Role READMEs and `CLAUDE.md` accurately reflect shipping defaults.
  Auditors and operators reading the docs see what the playbook will
  actually configure.
- The PR template explicitly asks contributors to confirm default/doc
  parity, reducing the rate at which F2-class drift re-accumulates.
- F4.* opportunities are explicit backlog items; the next validation
  pass starts from this list rather than re-discovering them.

## References

- `docs/compliance-controls.yml` — control catalog and policy set
- CIS Ubuntu Linux 24.04 Benchmark — auditd, sysctl, login.defs, mount
  option baselines
- BSI TR-02102-4 — recommended SSH algorithms
- `sshd_config(5)`, `chrony.conf(5)`, `pam_faillock(8)`,
  `pam_pwquality(8)`, `auditctl(8)` — option syntax and semantics
- Ansible production-profile lint rules — FQCN, `no-changed-when`
- NIS2 Directive (EU 2022/2555) Art 20–23
- Austrian NISG 2026 (transposition, effective 2026-10-01)
- Cyber Resilience Act (EU 2024/2847) Annex I
- GDPR (EU 2016/679) Art 5, 25, 32
- ISO/IEC 27001:2022 Annex A
