# Security Policy

Security fixes apply to the current `main` branch only.

## In scope

- Unencrypted secrets, credentials, or private keys committed to the
  repository
- Insecure default values in role `defaults/main.yml` that would weaken
  the hardening baseline
- Privilege-escalation defects in roles — unscoped `become`, untrusted
  input to `shell` / `command`, missing `validate:` on security-critical
  templates
- Missing hardening in playbooks (SSH, firewall, auditd) that would
  cause `playbooks/site-common.yml` to leave a host less hardened than
  the documented baseline
- Compliance-control regressions — a CTL-/POL- mapping that no longer
  matches the role's shipping behaviour

## Reporting

[GitHub private vulnerability reporting](https://github.com/rmednitzer/automation/security/advisories/new).
Include the affected file path, line numbers, reproduction steps, and
an impact assessment (with the affected CTL-/POL- ID, if applicable).

Acknowledgement within 5 business days; remediation timeline within 14
days.

## Best practices for contributors

- Never commit unencrypted secrets, passwords, API keys, or private
  keys. Use `ansible-vault` for sensitive data.
- Reference vault variables with a `vault_` prefix.
- Use FQCNs for all module calls.
- `become: true` only on tasks that need privilege; never globally.
- `changed_when` / `failed_when` on `shell` and `command` tasks so
  reported state matches reality.
- `validate:` on security-critical config templates (`sshd_config`,
  sudoers) so a typo cannot leave a broken file in place.
