# CLAUDE.md - AI Assistant Guide for automation

## Project Overview

This is the Ansible automation repository (formerly `ansible-ops`) — fleet hardening, configuration management, and operator-host toolchain provisioning, aligned with EU and Austrian regulatory requirements. Licensed under the Apache License 2.0.

The repository is intentionally tool-named rather than function-named: it owns everything Ansible does, including but not limited to system hardening. Companion repositories: `infra` (OpenTofu provisioning) and `runbooks` (ad-hoc operator scripts for recurring ops tasks).

## Compliance Alignment

This repository implements technical controls mapped to:

- **NIS2 Directive (EU 2022/2555)** — Art 20-23: risk management, incident handling, reporting
- **NISG 2026 (Austrian transposition)** — effective 2026-10-01
- **Cyber Resilience Act (EU 2024/2847)** — Annex I: secure-by-design
- **GDPR (EU 2016/679) / Austrian DSG** — Art 5, 25, 32: data protection by design
- **ISO/IEC 27001:2022** — Annex A controls

Controls and policies are defined locally in `docs/compliance-controls.yml`:
- Control catalog: `CTL-001`, `CTL-002`, `CTL-003`
- ISMS policies: `POL-001`, `POL-002`, `POL-003`, `POL-004`, `POL-005`

When modifying roles, preserve compliance cross-references in `defaults/main.yml` headers.
When adding new controls, map them to the relevant regulatory articles and add definitions to `docs/compliance-controls.yml`.

## Repository Structure

This repository follows the standard Ansible best-practices layout:

```
automation/
├── CLAUDE.md              # This file - AI assistant guide
├── LICENSE                # Apache License 2.0
├── README.md              # Project documentation
├── .gitignore             # Git ignore rules
├── ansible.cfg            # Ansible configuration
├── requirements.yml       # Ansible Galaxy dependencies (roles/collections)
├── inventories/           # Inventory files organized by environment
│   ├── production/
│   │   ├── hosts          # Production host definitions
│   │   ├── group_vars/    # Production group variables
│   │   └── host_vars/     # Production host-specific variables
│   ├── staging/
│   │   ├── hosts
│   │   ├── group_vars/
│   │   └── host_vars/
│   └── development/
│       ├── hosts
│       ├── group_vars/
│       └── host_vars/
├── playbooks/             # Top-level playbooks
├── roles/                 # Custom Ansible roles
│   └── <role_name>/
│       ├── tasks/
│       ├── handlers/
│       ├── templates/
│       ├── files/
│       ├── vars/
│       ├── defaults/
│       ├── meta/
│       └── README.md
├── group_vars/            # Global group variables
│   └── all.yml
├── host_vars/             # Global host-specific variables
├── plugins/               # Custom plugins
│   ├── filter/
│   ├── modules/
│   └── lookup/
├── files/                 # Static files used by playbooks
└── templates/             # Jinja2 templates used by playbooks
```

## Current State

The repository contains:

- A compliance-aligned hardening baseline of 10 roles applied to all fleet hosts by `playbooks/site-common.yml`: `common`, `users`, `ntp`, `ssh_hardening`, `ufw`, `fail2ban`, `aide`, `rkhunter`, `log_forwarding`, `auditd`.
- An operator-host toolchain role (`sre_toolchain`) invoked by `playbooks/sre-toolchain.yml`, installing pinned-to-latest SRE/Platform/Security binaries from upstream GitHub releases with SHA256 verification. This is **not** part of the hardening baseline — it targets only operator hosts (workstations, admin/bastion VMs, CI runners).

Target OS for every role: Ubuntu 24.04 LTS.

The codebase is periodically re-validated against known-good sources (CIS Ubuntu Benchmark, BSI TR-02102-4, upstream OpenSSH / chrony / auditd / pam_faillock / pam_pwquality manuals, Ansible production-profile lint rules). The latest baseline and its findings are recorded in [`docs/ADR-001-code-validation-baseline.md`](docs/ADR-001-code-validation-baseline.md). When opening a new ADR, increment the number and follow the same structure (Status, Date, Context, Decisions, Consequences, References).

## Development Conventions

### Naming Conventions

- **Roles**: Use lowercase with underscores (e.g., `nginx_proxy`, `postgresql_server`)
- **Playbooks**: Use lowercase with hyphens (e.g., `deploy-app.yml`, `setup-monitoring.yml`)
- **Variables**: Use lowercase with underscores, prefixed by role name (e.g., `nginx_listen_port`, `postgres_max_connections`)
- **Files/Templates**: Use lowercase with hyphens or underscores, matching the target filename
- **Inventory groups**: Use lowercase with underscores (e.g., `web_servers`, `db_servers`)
- **Tags**: Use lowercase with hyphens (e.g., `install-packages`, `configure-service`)

### YAML Style

- Use `.yml` extension (not `.yaml`)
- Use 2-space indentation
- Always use `true`/`false` for booleans (not `yes`/`no`)
- Quote strings that contain special YAML characters or could be misinterpreted
- Start every YAML file with `---`
- Use block style (`key: value`) over flow style (`{key: value}`)

### Ansible Best Practices

- Always name tasks descriptively (every `- name:` should explain what the task does)
- Use fully qualified collection names (FQCNs) for modules (e.g., `ansible.builtin.copy` not just `copy`)
- Prefer `ansible.builtin.template` over `ansible.builtin.copy` for config files that need variable substitution
- Use `become: true` only when needed, not globally
- Keep secrets in Ansible Vault encrypted files; never commit plaintext secrets
- Use `ansible.builtin.import_tasks` for static includes and `ansible.builtin.include_tasks` for dynamic includes
- Use handlers for service restarts/reloads triggered by configuration changes
- Set `changed_when` and `failed_when` on shell/command tasks to ensure accurate reporting

### Role Structure

Every role should include:
- `defaults/main.yml` - Default variables (overridable)
- `tasks/main.yml` - Main task list
- `handlers/main.yml` - Handlers (if needed)
- `meta/main.yml` - Role metadata and dependencies
- `README.md` - Role documentation

### Variable Precedence

Follow Ansible's variable precedence. Prefer defining variables at these levels:
1. `roles/<role>/defaults/main.yml` - Role defaults (lowest precedence, most overridable)
2. `group_vars/` - Group-specific overrides
3. `host_vars/` - Host-specific overrides
4. Playbook `vars:` - Playbook-level overrides (use sparingly)

### Secrets Management

- Use `ansible-vault` for encrypting sensitive data
- Store vault-encrypted files with a `vault_` prefix (e.g., `vault_secrets.yml`)
- Never commit unencrypted secrets, passwords, API keys, or private keys
- Reference vault variables with a `vault_` prefix in variable names

## Common Commands

```bash
# Check syntax of a playbook
ansible-playbook playbooks/<playbook>.yml --syntax-check

# Dry-run a playbook (check mode)
ansible-playbook -i inventories/<env>/hosts playbooks/<playbook>.yml --check --diff

# Run a playbook
ansible-playbook -i inventories/<env>/hosts playbooks/<playbook>.yml

# Run with specific tags
ansible-playbook -i inventories/<env>/hosts playbooks/<playbook>.yml --tags "tag1,tag2"

# Lint all YAML/Ansible files
ansible-lint
yamllint .

# Encrypt a file with vault
ansible-vault encrypt <file>

# View an encrypted file
ansible-vault view <file>

# Install Galaxy dependencies
ansible-galaxy install -r requirements.yml
```

## Quality Tools

When adding CI or local tooling, use:
- **ansible-lint** - Ansible-specific linting
- **yamllint** - YAML syntax and style checking
- **molecule** - Role testing framework (if testing roles in isolation)

## Git Workflow

- Branch from `main` for feature work
- Use descriptive branch names (e.g., `feature/add-nginx-role`, `fix/postgres-permissions`)
- Write clear commit messages describing the "why" of changes
- Keep commits focused on a single logical change

## Important Notes for AI Assistants

- Always read existing files before modifying them
- Never commit plaintext secrets or credentials
- When creating new roles, follow the full role structure outlined above
- When modifying inventory, be careful about environment separation
- Prefer idempotent operations in all Ansible tasks
- Test playbooks with `--check --diff` before actual runs when possible
- Use FQCNs for all module references
