# `common` role

Base system management and hardening for Ubuntu 24.04 LTS (Noble Numbat).

## What it does

- Installs the base package set and applies `apt upgrade --safe`
- Sets timezone (UTC by default — CTL-003 forensic correlation) and
  locale
- Applies a sysctl baseline (network, VM, file-handles, hardlink /
  symlink protection, IPv4 / IPv6 hardening, IPv6 privacy extensions
  per GDPR Art 5(1)(c))
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
| `common_sysctl_settings` | network / VM / FS / IPv4 / IPv6 hardening (see defaults) | Dict of sysctl key/value pairs |
| `common_journal_max_size` | `500M` | `SystemMaxUse` for `systemd-journald` |
| `common_journal_max_retention` | `6month` | `MaxRetentionSec` for `systemd-journald` |
| `common_motd_enabled` | `true` | Deploy the MOTD banner |
| `common_kernel_modules_blacklist` | `cramfs`, `freevxfs`, `hfs`, `hfsplus`, `jffs2`, `udf`, `usb-storage`, `dccp`, `sctp`, `rds`, `tipc` | Modules blacklisted by `modprobe` |
| `common_harden_tmp` | `true` | Write `tmpfs` `/tmp` and `/var/tmp` bind entries |
| `common_tmp_size` | `2G` | `tmpfs` size for `/tmp` |
| `common_harden_tmp_remount` | `false` | Remount immediately on apply (off — live remount discards `/tmp` and disrupts open file handles; safe on fresh hosts only) |
| `common_disable_core_dumps` | `true` | Disable core dumps (POL-004) |
| `common_services_disable` | `apport`, `whoopsie` | Services to stop / disable / mask |
| `common_log_retention` | `governance: 3650`, `incidents: 1825`, `ci: 1095`, `dr_tests: 1825`, `security_audit: 365`, `operational: 90` | Retention (days) per evidence tier (CTL-002 / CTL-003) |

Full list in `defaults/main.yml`.
