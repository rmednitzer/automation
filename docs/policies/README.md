# ISMS policy set (POL-*)

Navigation index for the ISMS policies referenced from
[`docs/compliance-controls.yml`](../compliance-controls.yml). The YAML
file is **canonical** — titles, descriptions, regulatory mappings, and
role coverage live there. This index is a convenience view for human
readers; it must not duplicate or override the YAML.

When a policy is added, renumbered, or retired, update
[`docs/compliance-controls.yml`](../compliance-controls.yml) first; the
table below is a derived summary.

| ID      | Title                                  | Roles |
|---------|----------------------------------------|-------|
| POL-001 | Access control policy                  | `ssh_hardening`, `users`, `ufw`, `apparmor`, `usbguard`, `nftables_egress`, `redfish` |
| POL-002 | Incident response policy               | `fail2ban`, `aide`, `rkhunter`, `ntp`, `log_forwarding`, `sre_toolchain`, `wazuh_agent` |
| POL-003 | Cryptography policy                    | `ssh_hardening`, `users`, `ntp`, `log_forwarding`, `aide`, `dns`, `vector` |
| POL-004 | Data classification and handling       | `common`, `auditd`, `systemd_hardening`, `kernel_lockdown`, `ollama` |
| POL-005 | Change management policy               | `auditd` |

## Related

- [Controls (CTL-*) index](../controls/README.md)
- [Evidence index](../evidence/README.md)
- [Compliance controls catalog](../compliance-controls.yml)
- [ADR-001 — code validation baseline](../ADR-001-code-validation-baseline.md)
