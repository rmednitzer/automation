# rkhunter Role

Rootkit detection via rkhunter for Ubuntu 24.04 LTS.

## What it does

- Installs rkhunter (Rootkit Hunter)
- Deploys a hardened `/etc/rkhunter.conf` aligned with POL-002 / NIS2
  Art 21.2(a)(b) / ISO 27001 A.8.7
- Runs `rkhunter --propupd` on first deploy to baseline the
  known-good property database
- Schedules a daily scan via cron (default 03:00) that emails the
  report when a `Warning` line is present and `rkhunter_mailto` is set
- Optionally installs an APT post-invoke hook that re-runs `propupd`
  after every `dpkg` operation — **disabled by default** because
  silent re-baselining defeats the point of integrity checking
- Configures logrotate for `/var/log/rkhunter.log` (weekly, 52
  rotations ≈ 1 year)

## Key Variables

| Variable                              | Default                                                                       | Description |
|---------------------------------------|-------------------------------------------------------------------------------|-------------|
| `rkhunter_enabled`                    | `true`                                                                        | Master enable switch |
| `rkhunter_cron_enabled`               | `true`                                                                        | Schedule daily scans |
| `rkhunter_cron_schedule`              | `0 3 * * *`                                                                   | Cron schedule (daily at 03:00) |
| `rkhunter_report_path`                | `/var/log/rkhunter.log`                                                       | Scan log path |
| `rkhunter_mailto`                     | `""`                                                                          | Email recipient for warnings (empty disables mail) |
| `rkhunter_update_db`                  | `true`                                                                        | Run `propupd` on deploy |
| `rkhunter_apt_hook`                   | `false`                                                                       | Install APT post-invoke `propupd` hook (off by default — see role defaults rationale) |
| `rkhunter_enable_tests`               | `all`                                                                         | `ENABLE_TESTS` value |
| `rkhunter_disable_tests`              | `suspscan hidden_ports hidden_procs deleted_files packet_cap_apps`            | Tests known to false-positive on Ubuntu |
| `rkhunter_allow_script_whitelisting`  | `true`                                                                        | Allow `SCRIPTWHITELIST` entries |
| `rkhunter_scriptwhitelist`            | `/usr/bin/{egrep,fgrep,which,ldd}`                                            | Known-good script replacements |
| `rkhunter_allowhiddendir`             | `/dev/.udev`, `/dev/.static`, `/dev/.initramfs`                               | Allowed hidden directories on Ubuntu |
| `rkhunter_allowhiddenfile`            | `/dev/.blkid.tab`, `/dev/.blkid.tab.old`                                      | Allowed hidden files on Ubuntu |

See `defaults/main.yml` for the full list.
