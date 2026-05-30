# `auditd` role

System audit logging via auditd for Ubuntu 24.04 LTS and 26.04 LTS
(ADR-004).

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
| `auditd_manage_runtime` | `true` | Manage the running daemon (start/enable, load rules, reload config). Auto-disabled inside containers (the audit subsystem is host-global/not namespaced, so auditd can't start and `auditctl`/`augenrules` fail); `auditd.conf` + rules are still deployed. Set `false` to force config-only |

Full list in `defaults/main.yml`.

## Testing

A Molecule scenario (`molecule/default/`) converges the role on Ubuntu
24.04 and 26.04 (ADR-004) and asserts the rules file deploys with the
`execve` accounting rule (key `exec`), the identity / sudoers / `plugins.d`
watches, no dead `/etc/audisp/` watch, and `auditd.conf` with
`log_format = ENRICHED`. It sets `auditd_immutable: false` so a second
converge reconciles without a reboot. The audit subsystem is host-global,
so the scenario asserts deployed artifacts, not live kernel rules. Run
`make molecule` on a Docker host (unrun in the authoring sandbox — see
`LIMITATIONS.md` L2/L3).
