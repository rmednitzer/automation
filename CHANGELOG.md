# Changelog

Format: [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

PRs touching roles, playbooks, or
[`docs/compliance-controls.yml`](./docs/compliance-controls.yml) must add
an `[Unreleased]` entry naming affected CTL- / POL- IDs.

## [Unreleased]

- 2026-06-10 **First live Molecule run — LIMITATIONS L2 closed; the CI
  Molecule matrix now gates on push/PR.** All four baseline scenarios
  (`users`, `ssh_hardening`, `auditd`, `common`) passed their first full
  `molecule test` (converge + idempotence + verify) on a real Docker host,
  dual-OS noble + resolute, after fixing what the live run surfaced:
  - **`users` (CTL-001/POL-001 relevant): real PAM ordering bug, not
    container noise.** The `pam_unix remember=` history edit ran *before*
    `pam-auth-update --enable faillock…`; editing a managed `common-*` file
    marks the stack locally modified, after which `pam-auth-update` refuses
    (exit 0) and faillock is silently never wired — on ANY host, fleet
    included. Caught by the role's own POL-001 assert; the `remember=` edit
    now runs last. The scenario also gained a `prepare.yml` resetting the
    geerlingguy images' pre-modified PAM baseline, and `libpam-pwquality`
    installs with `update_cache` (empty container apt caches; same fix for
    `openssh-server` in `ssh_hardening`).
  - **`common`: container-aware sysctl live-reload.** New
    `common_sysctl_reload` default (mirrors `auditd_runtime_managed`)
    disables the `sysctl -p` whole-file reload inside containers, where
    kernel-global keys (e.g. `net.core.rmem_max`) are read-only — the
    persisted drop-in is still written and verified. On real hosts,
    behaviour unchanged.
  - **`common`: probe-gated kernel-dependent knobs.**
    `kernel.unprivileged_userns_clone` (Ubuntu-only patch) and
    `kernel.yama.ptrace_scope` (needs Yama) now use the same
    probe-then-apply treatment as the optional sysctl map, replacing a
    blanket `failed_when: false`; the drop-in prune whitelist is now
    presence-aware so a stale key from an older kernel is pruned instead of
    breaking a later reload.
  - **`common`: minimal-host robustness.** `/etc/modprobe.d` ensured before
    writing blacklists; systemd coredump config moved from `lineinfile` on
    the (possibly absent) stock `coredump.conf` to a
    `coredump.conf.d/99-ansible.conf` drop-in; sensitive-file permission
    loop stat-gates optional files (`/etc/ssh/sshd_config`); the cron
    restart handler tolerates exactly the service-not-found case.
  - **`ssh_hardening`: `sshd -t` works pre-first-start.** The privilege-
    separation directory (`/run/sshd`) is pre-created so config validation
    does not depend on the service having started.
  - **Scenarios:** `ANSIBLE_ROLES_PATH` set in every scenario's provisioner
    (Molecule no longer injects the role's parent dir); the `common`
    verifier's `key = value` assertions made whitespace-agnostic (the
    drop-in is written as `key=value`) and its `ptrace_scope` check gated on
    Yama presence — the absent-key "not in drop-in" assertions were passing
    vacuously before.
  - **CI:** the `molecule` matrix's `workflow_dispatch`-only condition is
    removed — it gates on every push/PR (45-min timeout, `needs: lint`).
    The egress-heavy `sre_toolchain` scenario stays out of the matrix
    (LIMITATIONS L5; `make molecule-sre` on-demand). LIMITATIONS L3 updated
    (idempotence now live-exercised), L7 unblocked (tag `0.1.0` after the
    first green gating run on `main`).

- 2026-05-31 **Docs polish — sync the derived compliance indexes and enforce
  it.** `docs/controls/README.md` and `docs/policies/README.md` are convenience
  views that mirror the role coverage in `docs/compliance-controls.yml`, but
  they had fallen 11 roles behind (the role growth was mapped in the canonical
  YAML and validated, but never propagated to these hand-maintained tables):
  CTL-002/003 and POL-001/002/003/004 role lists are now back in sync. Added
  **rule 10** to `scripts/validate-compliance-controls.py` — each CTL-/POL- row
  in those indexes must equal the canonical YAML role set, so they can't drift
  again (verified the check fires). Also refreshed the stale "molecule —
  placeholder" line in `.github/copilot-instructions.md` (real `molecule/default`
  scenarios ship) to match `CLAUDE.md`. No control mappings or role logic
  changed.

- 2026-05-31 **Docs alignment — bring the Markdown in step with the code
  (no behaviour change).** The repo grew to 22 roles / 4 playbooks while the
  docs still described the original 10-role / 2-playbook baseline. Refreshed
  `CLAUDE.md` (the current-state baseline is now the accurate 19 site-common
  roles incl. opt-in `vector`/`wazuh_agent`, plus `sre_toolchain`/`ollama`/
  `redfish` in their own playbooks; the layout and the "molecule placeholder"
  note are corrected — real `molecule/default` scenarios exist). Expanded the
  `README.md` Roles table from 11 to all 22 roles (in site-common order) and
  added the missing ADR-005/006/007 rows. Fixed seven role READMEs whose
  tagline still said "Ubuntu 24.04 LTS" to "24.04 LTS and 26.04 LTS (ADR-004)",
  matching the dual-support already declared in every role's `meta`. No control
  mappings, role logic, or playbooks changed.

- 2026-05-31 **Regulatory framework coverage — map CRA Annex I and NISG 2026
  (audit remediation).** `docs/compliance-controls.yml` declared five
  frameworks in scope (NIS2, NISG 2026, CRA Annex I, GDPR, ISO 27001) but every
  `regulatory_mapping` cited only NIS2 / GDPR / ISO — **CRA Annex I and NISG
  2026 were declared but unmapped**. Added the missing citations across
  **CTL-001/002/003** and **POL-001/002/003/004/005**: CRA citations point to
  Annex I, Part I (2)(a)-(m) (verified against EUR-Lex CELEX 32024R2847) — e.g.
  (2)(d) unauthorised-access→CTL-001/POL-001, (2)(e) encryption→POL-003/POL-004,
  (2)(g) minimisation→POL-004, (2)(j) attack-surface→POL-001, (2)(k)
  exploitation-mitigation→POL-002, (2)(l) record/monitor activity→
  CTL-002/CTL-003/POL-005; NISG 2026 entries reference the transposed NIS2
  article (Austrian §-numbering deliberately not pinned until verifiable). Added
  a **framework-coverage check (rule 9)** to
  `scripts/validate-compliance-controls.py` (`EXPECTED_FRAMEWORKS`) so a
  declared-but-unmapped framework now fails the build — the gap can't recur. No
  control's roles or scope changed; only the regulatory citations were
  completed.

- 2026-05-31 **Container-guest gating for `ntp` / `ufw` / `fail2ban` /
  `rkhunter`, plus server-side secret scanning (audit remediation).** Extends
  the container-awareness already in `auditd` / `log_forwarding` to the
  remaining host-level service roles so they converge cleanly on a container
  **guest** (and can join the molecule matrix once scenarios land — see the
  `molecule` job note in `ci.yml`). Each role computes a
  `<role>_runtime_managed` guest check (a container `ansible_virtualization_type`
  **and** `ansible_virtualization_role == 'guest'`) and **still installs
  packages and deploys config-as-code**, gating only the host-runtime steps:
  `ntp` skips starting/verifying chrony and its restart handler (the clock is
  host-global); `ufw` skips all netfilter operations (no `NET_ADMIN` in a
  guest); `fail2ban` skips the daemon start and restart handler while keeping
  `fail2ban-client -t` config validation; `rkhunter` skips the property
  baseline, the scheduled scan, and the post-apt re-baseline (host-namespaced
  scan). A container *host* (role `host`) still manages everything. Also adds a
  dedicated **`Secret Scan (gitleaks)`** CI job
  ([`.github/workflows/ci.yml`](./.github/workflows/ci.yml)) running a full
  working-tree `gitleaks dir` scan — the existing pre-commit `gitleaks` hook
  scans STAGED changes only, a no-op in a clean CI checkout — pinned by
  immutable image digest (gitleaks v8.30.1, matching the companion repos);
  `.gitleaks.toml` excludes the vendored, gitignored `collections/` tree
  (third-party deps, not our secrets). No control mappings change (CTL-003 and
  POL-002 remain implemented; only their runtime steps are gated in containers).

- 2026-05-31 **Audit remediation — 26.04 deployability + auditd handler
  collision (correctness).** Two HIGH-severity fixes from the multi-repo audit.
  (1) `playbooks/site-common.yml` and `playbooks/sre-toolchain.yml` asserted
  `ansible_distribution_version == "24.04"` and failed closed on 26.04 — making
  the repo's advertised 24.04/26.04 dual-support (ADR-004, every role's
  `meta`, the molecule matrix) **undeployable** on 26.04. The asserts now accept
  `["24.04", "26.04"]`. (2) `roles/log_forwarding` and `roles/auditd` both
  defined a handler literally named `Reload auditd configuration`; handler names
  are play-global, so `log_forwarding`'s (loaded later, **ungated**) shadowed
  `auditd`'s container-guest-gated handler — running an unconditional
  `service auditd restart` on a container guest and defeating auditd's
  container-safety. `log_forwarding`'s handler is renamed to `Reload auditd for
  log forwarding` and gated on a new `log_forwarding_runtime_managed` guest
  check. No control mappings change (CTL-003 unaffected).

- 2026-05-31 **Compliance posture export — the fleet → MCP bridge (ADR-007).**
  Final AI-native thread (Fleet↔MCP wiring). `scripts/export-compliance-posture.py`
  emits the fleet's compliance posture as a deterministic, versioned JSON
  artifact (`fleet-compliance-posture/v1`) — controls/policies, regulatory
  mappings, implementing roles, per-role baseline/conditional status, and
  framework tallies — derived from `docs/compliance-controls.yml` +
  `playbooks/site-common.yml`. It gives the AI layer (the Vertex MCP gateway)
  a stable, **read-only** contract instead of parsing Ansible, and exposes only
  compliance metadata (no inventory/secrets) so it is safe to serve. Output is
  sorted with no timestamp (reproducible/diffable); `validate-compliance-controls.py`
  remains authoritative. Added `make export-compliance` and a CI smoke test
  (must emit valid JSON). `docs/ADR-007` records the contract; the serving
  gateway lives on Vertex (out of repo). GDPR Art 5(2), ISO 27001:2022 A.5.36.

- 2026-05-31 **AI-in-CI — advisory compliance review via local inference
  (ADR-006).** Second AI-native capability. A new workflow
  (`.github/workflows/ai-compliance-review.yml`) + stdlib-only script
  (`scripts/ai-compliance-review.py`) run an LLM review of a PR's changed role
  compliance headers against the control catalog — using a **local Ollama
  endpoint**, so diffs never leave the estate for a hosted AI API (POL-004 data
  sovereignty, coherent with the `ollama` role). **Advisory and non-blocking**:
  any failure (no endpoint, unreachable, empty response) skips gracefully with
  `exit 0`; the deterministic `validate-compliance-controls.py` stays the
  authoritative gate. **Dormant** until `AI_REVIEW_OLLAMA_ENDPOINT` is set (like
  the aspirational `redfish` role); for sovereignty it runs on a self-hosted
  runner with access to the inference host. `docs/ADR-006` records the rationale.
  GDPR Art 25 / Art 44, ISO 27001:2022 A.8.9 / A.8.28.

- 2026-05-31 **New `ollama` role — local LLM inference runtime (POL-004).**
  First AI-native capability. Provisions [Ollama](https://ollama.com) on
  dedicated inference hosts (e.g. the GPU compute host) so inference stays
  **on-premises** — prompts/data never go to a third-party model API (GDPR Art
  25 / Art 44 data sovereignty). Pinned + checksum-verified install (GitHub
  release tgz via `get_url checksum:`, ADR-002 pattern — no `curl | sh`),
  `ollama` system user, and a **hardened, localhost-bound** systemd unit
  (`NoNewPrivileges`, `ProtectSystem=full`, …; moderate for GPU device access).
  Off by default; requires a pinned `ollama_version` + `ollama_checksum`
  (asserted). Optional model pulls; NVIDIA GPU auto-detected (CPU fallback,
  drivers not installed). Run via `playbooks/local-inference.yml`
  (`inference_hosts` group), NOT `site-common.yml`. Container-guest aware.
  Mapped to POL-004 in `docs/compliance-controls.yml`. GDPR Art 25 / Art 5(1)(f)
  / Art 44, NIS2 Art 21.2(e), ISO 27001:2022 A.5.12 / A.8.9.

- 2026-05-31 **New `redfish` role + ADR-005 — aspirational out-of-band (BMC)
  management (POL-001).** Forward-looking capability for when the fleet gains
  enterprise hardware with BMCs (iDRAC/iLO/XCC/OpenBMC). `docs/ADR-005` records
  the strategy: vendor-neutral Redfish over legacy IPMI, mandatory management-
  VLAN isolation, security-first defaults, and a NIST SP 800-193 firmware
  posture. The `redfish` role (driven from the control host via
  `community.general.redfish_*`, run by `playbooks/redfish-oob.yml`) ships
  **inert** — off by default, empty `redfish_bmcs`. Read-only inventory
  (system/firmware/thermal) is the default action; **power control is
  double-gated** (`redfish_action: power` *and* `redfish_confirm_state_change`).
  TLS verification on, vaulted per-BMC credentials, `no_log` on
  credential-bearing tasks. Not part of `site-common.yml` (it targets BMCs, not
  fleet hosts). Mapped to POL-001 in `docs/compliance-controls.yml`. CRA Annex I,
  NIS2 Art 21.2(d)(e), ISO 27001:2022 A.8.2 / A.8.9.

- 2026-05-31 **New `rsyslog_hardening` role — local rsyslog hardening
  (CTL-003).** Completes the logging capability ("Vector ships, rsyslog local").
  Deploys `/etc/rsyslog.d/00-hardening.conf`: restrictive create-modes
  (`$FileCreateMode 0640`, `$DirCreateMode 0750`, `$Umask 0027`), privilege drop
  (`$PrivDropToUser/Group syslog`), and `$RepeatedMsgReduction`. Validates the
  whole config with `rsyslogd -N1` before any restart (a bad drop-in aborts
  before the running daemon is touched), and audits for unintended network log
  reception (`imtcp`/`imudp`) — warn by default, opt-in hard-fail via
  `rsyslog_hardening_fail_on_network_input`. Acts only when rsyslog is present
  (journald-only hosts are skipped, no forced install); container-guest aware
  (`rsyslog_hardening_runtime_managed`); never touches the `log_forwarding` /
  `vector` forwarding config. Added to `site-common.yml` after the log shippers
  and mapped to CTL-003 in `docs/compliance-controls.yml`. NIS2 Art 21.2(a),
  GDPR Art 5(1)(c) / Art 5(1)(f), ISO 27001:2022 A.8.15.

- 2026-05-31 **New `vector` role — modern log shipper to SIEM (CTL-002,
  CTL-003).** Adds [Vector](https://vector.dev) (by Datadog) as the modern
  complement to the rsyslog-based `log_forwarding`: reads journald and ships to
  a configurable SIEM sink. Adds the Vector APT repo via a `signed-by` Datadog
  keyring — imports the documented Datadog key **set** (`vector_apt_key_urls`:
  current + rollover, so key rotation doesn't break apt), built in a staging
  copy whose fingerprints are checked against the optional allow-list
  (`vector_apt_key_fingerprints`) and installed atomically only when changed;
  deploys `/etc/vector/vector.yaml` from `vector_sources`/`_transforms`/`_sinks`,
  **validated with `vector validate`** before placement (`diff: false` so a sink
  secret never reaches `--diff`/CI logs). **Off by default**
  (`vector_enabled: false`); `site-common.yml` runs it only when enabled, and
  the role asserts `vector_sinks` is set (no safe default destination) — sink
  secrets are referenced via vault vars, nothing committed (public-repo-safe).
  Container-guest aware (`vector_runtime_managed`). Mapped to CTL-002 + CTL-003
  in `docs/compliance-controls.yml`. POL-003 (TLS in transit), NIS2 Art
  21.2(a)(b), GDPR Art 5(2) / Art 32, ISO 27001:2022 A.8.15 / A.8.16.

- 2026-05-30 **New `nftables_egress` role — default-deny egress filtering
  (POL-001).** Final defense-in-depth piece. Adds an allow-listed OUTBOUND
  policy with nftables in a **separate `inet fw_egress` table** that composes
  with ufw (ufw untouched), loaded by an `nftables-egress.service` unit.
  Off-by-default risk ladder (`nftables_egress_mode`): `off` deploys nothing;
  `observe` logs non-allow-listed egress without dropping; `enforce` drops it.
  **Lock-out-safe** — the chain always accepts loop-back and
  established/related, so enforce never breaks the inbound SSH/Ansible session;
  the ruleset is `nft -c` syntax-checked before it is applied. Allow-list
  defaults (DNS/NTP/HTTP/HTTPS/DHCP/ICMP) keep core host functions working under
  enforce; `nftables_egress_allow_extra` takes destination-specific rules.
  Container-guest aware (`nftables_egress_runtime_managed`). Added to
  `site-common.yml` after `ufw` and mapped to POL-001 in
  `docs/compliance-controls.yml`. CRA Annex I Part I, NIS2 Art 21.2(e),
  GDPR Art 5(1)(f), ISO 27001:2022 A.8.20 / A.8.21.

- 2026-05-30 **New `usbguard` role — USB device authorization (POL-001).**
  Defense-in-depth part 3. Installs USBGuard and **audits** the USB attack
  surface (count of connected devices via `usbguard generate-policy`,
  read-only); **opt-in** (`usbguard_enforce`, default false) it bootstraps an
  allow-list from currently-connected devices, deploys the daemon policy
  (`ImplicitPolicyTarget=block`, `InsertedDevicePolicy=apply-policy`) and starts
  the blocking daemon. Lock-out-aware: `PresentDevicePolicy`/`PresentController
  Policy=keep` never deauthorise already-attached devices (console keyboard,
  storage) — only **newly inserted** USB is filtered. Container-guest aware
  (`usbguard_runtime_managed`; USB authz is host-hardware only). Added to
  `site-common.yml` after `kernel_lockdown` and mapped to POL-001 in
  `docs/compliance-controls.yml` (default-deny device access control). CRA
  Annex I Part I, NIS2 Art 21.2(e), GDPR Art 5(1)(f) / Art 25,
  ISO 27001:2022 A.8.3 / A.7.10.

- 2026-05-30 **New `kernel_lockdown` role — kernel lockdown LSM (POL-004).**
  Defense-in-depth part 2. Audits the current lockdown level from
  `/sys/kernel/security/lockdown` (read-only) and, **opt-in**, sets
  `integrity` / `confidentiality` by appending `lockdown=<level>` to the kernel
  command line via an `/etc/default/grub.d/99-lockdown.cfg` drop-in (composing
  onto `GRUB_CMDLINE_LINUX`, not editing `/etc/default/grub`), regenerating
  `grub.cfg`. Safe-by-default: `kernel_lockdown_level` is empty (audit only, no
  cmdline change) and the role **never reboots** — a level change is flagged
  reboot-required and the audit shows current-vs-desired. Container-guest aware
  (`kernel_lockdown_runtime_managed`; lockdown is host-kernel only). Added to
  `site-common.yml` after `apparmor` and mapped to POL-004 in
  `docs/compliance-controls.yml`. CRA Annex I Part I, NIS2 Art 21.2(e),
  GDPR Art 5(1)(f) / Art 25, ISO 27001:2022 A.8.27.

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
