# `rkhunter` role

Rootkit detection via rkhunter for Ubuntu 24.04 LTS and 26.04 LTS (ADR-004).

## What it does

- Installs rkhunter (Rootkit Hunter)
- Deploys a hardened `/etc/rkhunter.conf` aligned with POL-002 / NIS2
  Art 21.2(a)(b) / ISO 27001 A.8.7
- Runs `rkhunter --propupd` on first deploy to baseline the known-good
  property database
- Schedules a daily scan via cron (default 03:00) that emails the
  report when a `Warning` line is present and `rkhunter_mailto` is set
- Optionally installs an APT post-invoke hook that re-runs `propupd`
  after every `dpkg` operation — **disabled by default** because
  silent re-baselining defeats the point of integrity checking
- Rotates `/var/log/rkhunter.log` (weekly, 52 rotations ≈ 1 year)

## Container guests

On a container **guest** rkhunter only sees the container's namespaced view
(host-kernel rootkits aren't assessable from inside, and many checks
false-positive). The role still installs the package and deploys its config and
logrotate, but **skips the file-property baseline, the scheduled scan, and the
post-apt re-baseline** under `rkhunter_runtime_managed`. Rootkit scanning is the
host's job; a container *host* scans itself normally.

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `rkhunter_enabled` | `true` | Master enable switch |
| `rkhunter_cron_enabled` | `true` | Schedule daily scans |
| `rkhunter_cron_schedule` | `0 3 * * *` | Cron schedule (daily at 03:00) |
| `rkhunter_report_path` | `/var/log/rkhunter.log` | Scan log path |
| `rkhunter_mailto` | `""` | Email recipient for warnings (empty disables mail) |
| `rkhunter_update_db` | `true` | Run `propupd` on deploy |
| `rkhunter_apt_hook` | `false` | Install APT post-invoke `propupd` hook (off by default — see role defaults rationale) |
| `rkhunter_enable_tests` | `all` | `ENABLE_TESTS` value |
| `rkhunter_disable_tests` | `suspscan hidden_ports hidden_procs deleted_files packet_cap_apps` | Tests known to false-positive on Ubuntu |
| `rkhunter_allow_script_whitelisting` | `true` | Allow `SCRIPTWHITELIST` entries |
| `rkhunter_scriptwhitelist` | list — `[/usr/bin/egrep, /usr/bin/fgrep, /usr/bin/which, /usr/bin/ldd]` | Known-good script replacements |
| `rkhunter_allowhiddendir` | list — `[/dev/.udev, /dev/.static, /dev/.initramfs]` | Allowed hidden directories on Ubuntu |
| `rkhunter_allowhiddenfile` | list — `[/dev/.blkid.tab, /dev/.blkid.tab.old]` | Allowed hidden files on Ubuntu |

Full list in `defaults/main.yml`.
