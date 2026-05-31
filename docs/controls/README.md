# Control catalog (CTL-*)

Navigation index for the technical controls referenced from
[`docs/compliance-controls.yml`](../compliance-controls.yml). The YAML
file is **canonical** — titles, descriptions, regulatory mappings,
retention tiers, and role coverage live there. This index is a
convenience view for human readers; it must not duplicate or override
the YAML.

When a control is added, renumbered, or retired, update
[`docs/compliance-controls.yml`](../compliance-controls.yml) first; the
table below is a derived summary.

| ID      | Title                                                | Roles |
|---------|------------------------------------------------------|-------|
| CTL-001 | Federated IAM with MFA and auditable authorization   | `ssh_hardening`, `users` |
| CTL-002 | Immutable evidence store with retention controls     | `auditd`, `aide`, `log_forwarding`, `common`, `sre_toolchain`, `wazuh_agent`, `vector` |
| CTL-003 | Logging legality, minimisation, and forensic correlation | `auditd`, `ntp`, `log_forwarding`, `common`, `vector`, `rsyslog_hardening` |

CTL-002 defines retention tiers; see
[evidence index](../evidence/README.md) for the on-host paths each tier
applies to.

## Related

- [Policies (POL-*) index](../policies/README.md)
- [Evidence index](../evidence/README.md)
- [Compliance controls catalog](../compliance-controls.yml)
- [ADR-001 — code validation baseline](../ADR-001-code-validation-baseline.md)
