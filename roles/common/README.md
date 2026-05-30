# `common` role

Base system management and hardening for Ubuntu 24.04 LTS (Noble Numbat)
and Ubuntu 26.04 LTS (Resolute Raccoon, kernel 7.0). See
[`docs/ADR-004-ubuntu-2604-dual-support.md`](../../docs/ADR-004-ubuntu-2604-dual-support.md)
for the dual-support stance.

## What it does

- Installs the base package set and applies `apt upgrade --safe`
- Sets timezone (UTC by default — CTL-003 forensic correlation) and
  locale
- Applies a sysctl baseline (network, VM, file-handles, hardlink /
  symlink protection, `protected_fifos` / `protected_regular`, IPv4 /
  IPv6 hardening, IP-forwarding and secure-redirects disabled, `kexec` /
  line-discipline-autoload / `perf_event_paranoid` restrictions per CIS,
  eBPF JIT hardening, `unprivileged_userfaultfd` disabled, IPv6 privacy
  extensions per GDPR Art 5(1)(c)). Router/NAT and profiling hosts
  override the relevant keys.
- Applies kernel-version-dependent sysctls when the knob exists on the
  running kernel (`kernel.io_uring_disabled`, `dev.tty.legacy_tiocsti`) —
  path-gated so the same baseline stays idempotent across kernel 6.8
  (24.04) and 7.0 (26.04); a missing knob is skipped, never a failure.
- Hardens the kernel: blacklists unused filesystem and network modules,
  disables core dumps, enables ASLR, restricts kernel pointer / dmesg
  / unprivileged BPF / unprivileged user namespaces / `ptrace_scope`
- Hardens the filesystem: writes a `tmpfs` fstab entry for `/tmp` with
  `noexec,nosuid,nodev`, bind-mounts `/var/tmp` to `/tmp`, sets the
  sticky bit on any world-writable directories found, and re-asserts
  permissions on
  `/etc/{shadow,gshadow,passwd,group,crontab}` and `/etc/ssh/sshd_config`
- Configures `systemd-journald` (size cap, retention, persistent
  storage, syslog forwarding)
- Configures `unattended-upgrades` with the security pocket only
- Disables Ubuntu bloat services (`apport`, `whoopsie`)
- Owns `/etc/logrotate.d/rsyslog` end-to-end with compliance-aligned
  retention tiers (avoids the historical "duplicate log entry" abort)
  and ships a dedicated `compliance-sudo` rotation
- Deploys a system-info MOTD banner (optional)

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `common_timezone` | `UTC` | System timezone |
| `common_locale` | `en_US.UTF-8` | System locale |
| `common_language` | `en_US.UTF-8` | System language |
| `common_packages` | base package set (see defaults) | Packages to install |
| `common_packages_remove` | `[]` | Packages to purge |
| `common_auto_updates_enabled` | `true` | Enable `unattended-upgrades` |
| `common_auto_updates_mail` | `""` | Mail recipient for `unattended-upgrades` |
| `common_auto_updates_reboot` | `false` | Auto-reboot after kernel updates |
| `common_auto_updates_reboot_time` | `02:00` | Reboot time when auto-reboot is enabled |
| `common_sysctl_settings` | network / VM / FS / IPv4 / IPv6 hardening (see defaults) | Dict of sysctl key/value pairs (applied unconditionally) |
| `common_sysctl_settings_optional` | `kernel.io_uring_disabled: 1`, `dev.tty.legacy_tiocsti: 0` | Kernel-version-dependent sysctls; applied only where the `/proc/sys` path exists (idempotent across 6.8 / 7.0) |
| `common_kernel_kptr_restrict` | `2` | `kernel.kptr_restrict` (hide kernel pointers — KSPP) |
| `common_kernel_dmesg_restrict` | `1` | `kernel.dmesg_restrict` (restrict dmesg — CIS 1.5.x) |
| `common_kernel_unprivileged_bpf_disabled` | `1` | `kernel.unprivileged_bpf_disabled` (KSPP / CIS) |
| `common_kernel_randomize_va_space` | `2` | `kernel.randomize_va_space` (full ASLR — KSPP) |
| `common_kernel_ptrace_scope` | `2` | `kernel.yama.ptrace_scope` (admin-only ptrace; CIS=2, KSPP=3) |
| `common_journal_max_size` | `500M` | `SystemMaxUse` for `systemd-journald` |
| `common_journal_max_retention` | `6month` | `MaxRetentionSec` for `systemd-journald` |
| `common_motd_enabled` | `true` | Deploy the MOTD banner |
| `common_kernel_modules_blacklist` | list — `[cramfs, freevxfs, hfs, hfsplus, jffs2, udf, usb-storage, dccp, sctp, rds, tipc]` | Modules blacklisted by `modprobe` |
| `common_harden_tmp` | `true` | Write `tmpfs` `/tmp` and `/var/tmp` bind entries |
| `common_tmp_size` | `2G` | `tmpfs` size for `/tmp` |
| `common_harden_tmp_remount` | `false` | Remount immediately on apply (off — live remount discards `/tmp` and disrupts open file handles; safe on fresh hosts only) |
| `common_disable_core_dumps` | `true` | Disable core dumps (POL-004) |
| `common_services_disable` | `apport`, `whoopsie` | Services to stop / disable / mask |
| `common_log_retention` | `governance: 3650`, `incidents: 1825`, `ci: 1095`, `dr_tests: 1825`, `security_audit: 365`, `operational: 90` | Retention (days) per evidence tier (CTL-002 / CTL-003) |

Full list in `defaults/main.yml`.

## Testing

A Molecule scenario (`molecule/default/`) converges the role on Ubuntu
24.04 and 26.04 (ADR-004) and asserts the kernel-7.0 / KSPP sysctl
additions (`bpf_jit_harden`, `protected_fifos`/`protected_regular`,
`unprivileged_userfaultfd`) and the overridable kernel-hardening sysctls
are written to `/etc/sysctl.d/90-ansible.conf`, and that every
path-gated optional knob present on the running kernel
(`io_uring_disabled`, `legacy_tiocsti`) was applied. It asserts the written
drop-in (always produced) rather than live values, since some kernel-global
sysctls are read-only in a container. Run `make molecule` on a Docker host
(unrun in the authoring sandbox — see `LIMITATIONS.md` L2/L3).
