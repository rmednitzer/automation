# Evidence index

Audit-facing view of the configuration artifacts the hardening baseline
produces on a managed host. Each artifact is mapped back to a control
(CTL-*) or policy (POL-*) in
[`docs/compliance-controls.yml`](../compliance-controls.yml) and to the
retention tier defined under CTL-002.

This file is a documentation view only. The artifacts themselves live
on the managed host, not in this repository.

## Artifacts produced by `playbooks/site-common.yml`

| Artifact path on managed host                                | Producing role  | CTL / POL                | Retention tier   |
|--------------------------------------------------------------|-----------------|--------------------------|------------------|
| `/var/log/audit/audit.log`                                   | `auditd`        | CTL-002, CTL-003, POL-005 | `governance`     |
| `/var/log/aide/aide-check-*.log`                             | `aide`          | CTL-002, POL-002         | `security_audit` |
| `/var/lib/aide/aide.db`                                      | `aide`          | CTL-002, POL-002         | `governance`     |
| `/var/log/rkhunter.log`                                      | `rkhunter`      | POL-002                  | `security_audit` |
| `/var/log/auth.log`, `/var/log/secure`                       | `common`, `ssh_hardening` | POL-001, CTL-003 | `security_audit` |
| `/etc/issue.net` (legal monitoring banner)                   | `ssh_hardening` | POL-001, GDPR Art 5(2)   | n/a (config)     |
| `/etc/audit/rules.d/*.rules`                                 | `auditd`        | CTL-003, POL-005         | n/a (config)     |
| `/etc/fail2ban/jail.d/*.local`                               | `fail2ban`      | POL-002                  | n/a (config)     |
| `/var/log/fail2ban.log`                                      | `fail2ban`      | POL-002                  | `security_audit` |
| Central log aggregator (set via `log_forwarding_server`)     | `log_forwarding` | CTL-002, CTL-003, POL-002, POL-003 | per aggregator policy |
| `/usr/local/bin/.sre-toolchain-versions.json`                | `sre_toolchain` | CTL-002, POL-002         | `governance`     |

## Retention tiers (CTL-002)

Defined in [`docs/compliance-controls.yml`](../compliance-controls.yml)
under `CTL-002.retention_tiers`.

| Tier               | Days   | Notes |
|--------------------|--------|-------|
| `governance`       | 3650   | 10 years; audit logs, AIDE database baselines |
| `incidents`        | 1825   | 5 years; incident records |
| `dr_tests`         | 1825   | 5 years; DR test artifacts |
| `ci`               | 1095   | 3 years; CI run outputs |
| `security_audit`   | 365    | 1 year; auth logs, integrity-scan reports |
| `operational`      | 90     | 90 days; routine operational logs |

The `common` role configures rotation via
`common_log_retention.<tier>` variables; defaults match the tiers
above.

## Related

- [Policies (POL-*) index](../policies/README.md)
- [Controls (CTL-*) index](../controls/README.md)
- [Compliance controls catalog](../compliance-controls.yml)
- [README — Evidence and audit](../../README.md#evidence-and-audit)
