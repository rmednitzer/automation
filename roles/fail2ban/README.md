# `fail2ban` role

Intrusion prevention via Fail2Ban for Ubuntu 24.04 LTS.

## What it does

- Installs Fail2Ban and deploys `/etc/fail2ban/jail.local`
- Enables the `sshd` jail (3-attempt limit by default)
- Uses `systemd` as the log backend (journal-based, no log-file race
  conditions)
- Uses UFW as the ban action so bans are enforced at the firewall layer
  (integrates with the `ufw` role)
- Enables the `recidive` jail (escalating bans for repeat offenders) by
  default — POL-002 P2 severity
- Supports custom jails and optional email notifications

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `fail2ban_ignoreip` | `127.0.0.1/8 ::1` | IPs to never ban |
| `fail2ban_bantime` | `6h` | Default ban duration |
| `fail2ban_findtime` | `10m` | Window over which `maxretry` is counted |
| `fail2ban_maxretry` | `5` | Default attempts before ban (per-jail can override) |
| `fail2ban_backend` | `systemd` | Log backend (journal-based) |
| `fail2ban_banaction` | `ufw` | Ban action (integrates with the `ufw` role) |
| `fail2ban_jails` | `sshd` (port `ssh`, `maxretry: 3`, `bantime: 6h`) | Jails to enable |
| `fail2ban_recidive_enabled` | `true` | Enable the `recidive` jail |
| `fail2ban_recidive_bantime` | `1w` | Recidive ban duration |
| `fail2ban_recidive_findtime` | `1d` | Recidive window |
| `fail2ban_recidive_maxretry` | `3` | Recidive trigger threshold |
| `fail2ban_custom_jails` | `[]` | Additional jails (raw key/value dicts) |
| `fail2ban_notify_email` | `""` | If set, send ban notifications |
| `fail2ban_sender_email` | `fail2ban@{{ ansible_fqdn }}` | Notification sender |

The `sshd` jail uses `port: ssh` (the `/etc/services` symbolic name).
If you change `ssh_port` in the `ssh_hardening` role, override
`fail2ban_jails` with the matching numeric port — otherwise the jail
protects port 22 while sshd listens elsewhere.

Full list in `defaults/main.yml`.
