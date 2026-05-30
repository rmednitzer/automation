# `systemd_hardening` role

Confines services with **systemd sandboxing** — capability, syscall,
filesystem and namespace restrictions applied per unit via drop-ins — and runs
a read-only **`systemd-analyze security`** exposure audit, on Ubuntu 24.04 /
26.04 LTS.

## What it does

- Ships two vetted, reusable hardening **profiles** (`local_daemon`,
  `network_daemon`) — bundles of `[Service]` sandboxing directives
  (`NoNewPrivileges`, `ProtectSystem=strict`, `PrivateTmp`,
  `ProtectKernel*`, `RestrictAddressFamilies`, `SystemCallFilter=@system-service`,
  `CapabilityBoundingSet`, …).
- Applies a profile to a unit **only when you opt that unit in** via
  `systemd_hardening_units`, writing
  `/etc/systemd/system/<unit>.d/10-hardening.conf` (drop-in — the packaged unit
  is never edited). Per-unit `overrides` extend or replace individual
  directives.
- Runs `systemd-analyze security` for a configurable unit list and reports each
  service's exposure score (read-only; optional CI/staging threshold gate).

## Safe by default

- **Nothing is applied fleet-wide until you opt a unit in.**
  `systemd_hardening_units` is empty by default, so a baseline run only executes
  the read-only audit and changes nothing on disk.
- **Staged, not bounced.** `systemd_hardening_restart_on_change` is `false` by
  default: a changed drop-in triggers a `daemon-reload` (so `systemctl show`
  reflects it) but the service is **not** restarted mid-run — the sandbox takes
  effect on its next natural restart/reboot. Set `restart: true` per unit (or
  flip the global flag) once you have validated the unit in staging.
- **Container-guest aware** (`systemd_hardening_runtime_managed`): in a
  container *guest* the daemon-reload, restarts and the audit are skipped
  (service sandboxing is the host systemd's job there) while the drop-in files
  are still written; a container/LXC **host** is managed normally — the same
  `ansible_virtualization_role == 'guest'` pattern as `auditd` / `dns`.

## Usage

Assign a profile to a unit in `group_vars`, overriding the directives that
specific service needs. Validate in staging, then enable `restart`:

```yaml
# inventories/<env>/group_vars/<group>.yml
systemd_hardening_units:
  fail2ban:
    profile: network_daemon
    overrides:
      # fail2ban edits nftables/iptables -> netlink + net caps; writes its db.
      RestrictAddressFamilies: "AF_UNIX AF_INET AF_INET6 AF_NETLINK"
      CapabilityBoundingSet: "CAP_NET_ADMIN CAP_NET_RAW CAP_DAC_READ_SEARCH"
      ReadWritePaths: "/var/lib/fail2ban /run/fail2ban"
  chrony:
    profile: network_daemon
    restart: true
    overrides:
      # chrony steers the clock -> must NOT ProtectClock; needs CAP_SYS_TIME.
      ProtectClock: "no"
      CapabilityBoundingSet: "CAP_SYS_TIME"
      ReadWritePaths: "/var/lib/chrony /run/chrony"
```

### Per-service caveats (read before opting a unit in)

Sandboxing is service-specific; the wrong directive silently breaks a daemon on
its next restart. The common traps:

| Directive | Breaks | Fix |
|-----------|--------|-----|
| `ProtectClock=yes` | time daemons (chrony) | set `no`, add `CAP_SYS_TIME` |
| `ProtectSystem=strict` | any daemon writing state | add `ReadWritePaths` |
| `CapabilityBoundingSet=` (empty) | daemons needing a capability | list the caps it needs |
| `RestrictAddressFamilies=AF_UNIX` | network daemons | add `AF_INET AF_INET6` (and `AF_NETLINK` for nft/iptables) |
| `MemoryDenyWriteExecute=yes` | JIT / interpreter services | omit for that unit |
| `PrivateDevices=yes` | services needing `/dev` nodes | omit / use `DeviceAllow` |

`network_daemon` therefore leaves `CapabilityBoundingSet` and
`MemoryDenyWriteExecute` **unset** (restrict per unit); `local_daemon` is the
strict profile (AF_UNIX only, all caps dropped, W^X enforced).

## Audit

`systemd_hardening_audit` (default `true`) runs `systemd-analyze security` for
`systemd_hardening_audit_units` and reports the exposure score per unit (units
with no unit file on a host are skipped, not failed). View the report with
`-v`. Set `systemd_hardening_audit_threshold` (e.g. `"9.5"`) to **fail** when a
unit's exposure exceeds it — useful as a staging/CI gate. The audit is
read-only and feeds the AI-assisted hardening review in the AI-native series.

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `systemd_hardening_enabled` | `true` | Master switch (audit-only until units opted in) |
| `systemd_hardening_units` | `{}` | Units to harden (opt-in): `profile` / `overrides` / `restart` / `unit` |
| `systemd_hardening_profiles` | `local_daemon`, `network_daemon` | Reusable directive bundles |
| `systemd_hardening_restart_on_change` | `false` | Restart a unit when its drop-in changes (else stage only) |
| `systemd_hardening_manage_runtime` | `true` | Manage reload/restart/audit (auto-off in container guests) |
| `systemd_hardening_audit` | `true` | Run the read-only `systemd-analyze security` report |
| `systemd_hardening_audit_units` | `ssh`, `chrony`, `fail2ban`, `systemd-resolved`, `systemd-journald`, `auditd` | Units to audit |
| `systemd_hardening_audit_threshold` | `""` | Fail when exposure exceeds this score (empty = report only) |

Full list in `defaults/main.yml`.

## Compliance

POL-004 (data classification & handling — service sandboxing prevents data
leaking via tmp/filesystem/exec, the same posture POL-004 asks of core dumps /
swap / temp files, applied at the service boundary). CRA Annex I Part I
(minimise attack surface), NIS2 Art 21.2(e), GDPR Art 25 / Art 5(1)(f),
ISO 27001:2022 A.8.27.
