# `ufw` role

UFW firewall management for Ubuntu 24.04 LTS.

## What it does

- Installs and enables UFW
- Sets default deny incoming / allow outgoing
- Rate-limits SSH to prevent brute-force
- Configures allow rules from a simple list
- Supports raw rules for complex scenarios
- Enables firewall logging

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ufw_default_incoming` | `deny` | Default incoming policy |
| `ufw_default_outgoing` | `allow` | Default outgoing policy |
| `ufw_rules` | SSH on port 22 | List of firewall rules |
| `ufw_rate_limit_ssh` | `true` | Rate-limit SSH connections |
| `ufw_logging` | `on` | Enable UFW logging |
| `ufw_raw_rules` | `[]` | Raw UFW rule strings |

Full list in `defaults/main.yml`.
