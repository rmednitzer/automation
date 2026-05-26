# `auditd` role

System audit logging via auditd for Ubuntu 24.04 LTS.

## What it does

- Installs `auditd` and `audispd-plugins`
- Deploys `/etc/audit/auditd.conf` with compliance-sized buffers, log
  rotation, and disk-space failure modes
- Deploys `/etc/audit/rules.d/99-ansible.rules` covering:
  - **CIS Benchmark** rules — time changes, user/group modifications,
    network configuration, logins/logouts, permission and ownership
    changes, unauthorised access attempts, privileged command usage,
    kernel module loading, file deletion, sudoers changes, audit
    configuration changes
  - **NIS2 / GDPR / CRA** extended rules — PAM/security configuration,
    filesystem mounts, cron/systemd scheduling, network/firewall
    configuration, crypto material, hostname/DNS, package management,
    crypto key generation, service management
  - User-supplied raw rules via `auditd_custom_rules`
- Makes the rule set immutable (`-e 2`) by default — CIS-recommended,
  locks rule changes until reboot (see defaults rationale)

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `auditd_buffer_size` | `16384` | Kernel ring buffer entries (`-b`) |
| `auditd_backlog_limit` | `16384` | Backlog queue depth |
| `auditd_max_log_file` | `100` | Maximum log file size (MB) |
| `auditd_max_log_file_action` | `rotate` | Action when `max_log_file` is reached |
| `auditd_num_logs` | `20` | Number of rotated log files retained |
| `auditd_log_format` | `ENRICHED` | Log format (`auditd.conf`) |
| `auditd_failure_mode` | `1` | `0` silent / `1` printk / `2` panic |
| `auditd_space_left` | `150` | Low-space threshold (MB) |
| `auditd_space_left_action` | `SYSLOG` | Action at low-space threshold |
| `auditd_admin_space_left` | `75` | Admin low-space threshold (MB) |
| `auditd_admin_space_left_action` | `SUSPEND` | Action at admin low-space threshold |
| `auditd_disk_full_action` | `SUSPEND` | Action when disk is full |
| `auditd_disk_error_action` | `SUSPEND` | Action on disk error |
| `auditd_cis_rules` | `true` | Emit CIS-aligned rule block |
| `auditd_compliance_rules` | `true` | Emit NIS2/GDPR extended rule block |
| `auditd_custom_rules` | `[]` | Raw `auditctl` lines appended verbatim |
| `auditd_immutable` | `true` | Append `-e 2` to lock the rule set until reboot |

Full list in `defaults/main.yml`.
