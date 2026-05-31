# `aide` role

File integrity monitoring via AIDE for Ubuntu 24.04 LTS and 26.04 LTS (ADR-004).

## What it does

- Installs AIDE (Advanced Intrusion Detection Environment)
- Deploys a hardened AIDE configuration monitoring critical directories
- Initialises the AIDE database on first run
- Schedules daily integrity checks via cron
- Rotates AIDE reports
- Optionally emails reports on completion

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `aide_enabled` | `true` | Enable AIDE |
| `aide_db_path` | `/var/lib/aide/aide.db` | AIDE database path |
| `aide_cron_enabled` | `true` | Schedule daily checks |
| `aide_cron_schedule` | `0 4 * * *` | Cron schedule (daily at 04:00) |
| `aide_report_path` | `/var/log/aide/aide-check.log` | Report output path |
| `aide_mailto` | `""` | Email recipient for reports |
| `aide_monitored_dirs` | `/etc, /usr/bin, /usr/sbin, /usr/lib, /boot` | Directories to monitor |
| `aide_excluded_dirs` | `/etc/mtab, /etc/adjtime, /etc/resolv.conf` | Paths to exclude |
| `aide_init_db` | `true` | Initialise database on first run |

Full list in `defaults/main.yml`.
