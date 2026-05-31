# `ntp` role

Time synchronisation via `chrony` for Ubuntu 24.04 LTS.

## What it does

- Removes `systemd-timesyncd` to avoid two daemons fighting over the
  system clock
- Installs and configures `chrony`
- Defaults to Austrian / European NTP pools for jurisdictional
  alignment with NISG 2026
- Optionally enables NTS (Network Time Security) for
  cryptographically-authenticated time (POL-003)
- Polls `chronyc tracking` after start with retries so the role
  tolerates the brief race between `systemctl start chrony` and
  responsiveness

## Container guests

On a container **guest** (a container `ansible_virtualization_type` with
`ansible_virtualization_role == guest`) the system clock belongs to the host
and `chronyd` cannot step it. The role still installs `chrony` and deploys its
config (config-as-code) but **skips starting/verifying the daemon** and the
restart handler (`ntp_runtime_managed`). A container *host* manages time
normally.

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ntp_servers` | list — `["0.at.pool.ntp.org iburst", "1.at.pool.ntp.org iburst", "2.at.pool.ntp.org iburst", "0.europe.pool.ntp.org iburst"]` | Discrete NTP servers (each entry is a full `chrony.conf` `server` line) |
| `ntp_pools` | `[]` | NTP pool entries (alternative to discrete servers) |
| `ntp_allow_networks` | `[]` | Networks permitted to query as clients (empty = server-only mode) |
| `ntp_driftfile` | `/var/lib/chrony/chrony.drift` | Drift file path |
| `ntp_logdir` | `/var/log/chrony` | Log directory |
| `ntp_rtcsync` | `true` | Enable kernel RTC sync |
| `ntp_makestep_threshold` | `1.0` | Step threshold (seconds) |
| `ntp_makestep_limit` | `3` | Step operations permitted at startup |
| `ntp_nts_enabled` | `false` | Enable NTS-authenticated time |
| `ntp_nts_servers` | `[]` | NTS server list (e.g. `time.cloudflare.com nts iburst`) |

Full list in `defaults/main.yml`.
