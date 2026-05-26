# Copilot Instructions for automation

`automation` is the Ansible automation repository — fleet hardening, configuration management, and operator-host toolchain provisioning. Companion repositories: `infra` (OpenTofu) and `runbooks` (ad-hoc operator scripts).

## Repository Layout

Standard Ansible best-practices layout with `inventories/<env>/` (production, staging, development, each with their own `group_vars/` and `host_vars/`), `playbooks/`, `roles/`, and a global `group_vars/all.yml`. Files and templates live inside each role (`roles/<role>/files/`, `roles/<role>/templates/`) — there is no top-level `files/`, `templates/`, `host_vars/`, or `plugins/` directory. Plugin subdirectories should only be created on demand alongside the matching `ansible.cfg` plugin-path setting. See `CLAUDE.md` for the full structure.

## Naming Conventions

- **Roles**: lowercase with underscores (`nginx_proxy`, `postgresql_server`)
- **Playbooks**: lowercase with hyphens (`deploy-app.yml`, `setup-monitoring.yml`)
- **Variables**: lowercase with underscores, prefixed by role name (`nginx_listen_port`, `postgres_max_connections`)
- **Files/Templates**: lowercase with hyphens or underscores, matching the target filename
- **Inventory groups**: lowercase with underscores (`web_servers`, `db_servers`)
- **Tags**: lowercase with hyphens (`install-packages`, `configure-service`)

## YAML Style

- Use `.yml` extension (not `.yaml`)
- Use 2-space indentation
- Always use `true`/`false` for booleans (not `yes`/`no`)
- Quote strings that contain special YAML characters or could be misinterpreted
- Start every YAML file with `---`
- Use block style (`key: value`) over flow style (`{key: value}`)

## Ansible Best Practices

- Always name tasks descriptively (every `- name:` should explain what the task does)
- Use fully qualified collection names (FQCNs) for modules (e.g., `ansible.builtin.copy` not just `copy`)
- Prefer `ansible.builtin.template` over `ansible.builtin.copy` for config files that need variable substitution
- Use `become: true` only when needed, not globally
- Keep secrets in Ansible Vault encrypted files; never commit plaintext secrets
- Use `ansible.builtin.import_tasks` for static includes and `ansible.builtin.include_tasks` for dynamic includes
- Use handlers for service restarts/reloads triggered by configuration changes
- Set `changed_when` and `failed_when` on shell/command tasks to ensure accurate reporting
- Prefer idempotent operations in all Ansible tasks

## Role Structure

Every role should include:
- `defaults/main.yml` - Default variables (overridable)
- `tasks/main.yml` - Main task list
- `handlers/main.yml` - Handlers (if needed)
- `meta/main.yml` - Role metadata and dependencies
- `README.md` - Role documentation

## Variable Precedence

1. `roles/<role>/defaults/main.yml` - Role defaults (lowest precedence)
2. `group_vars/` - Group-specific overrides
3. `host_vars/` - Host-specific overrides
4. Playbook `vars:` - Playbook-level overrides (use sparingly)

## Secrets Management

- Use `ansible-vault` for encrypting sensitive data
- Store vault-encrypted files with a `vault_` prefix (e.g., `vault_secrets.yml`)
- Never commit unencrypted secrets, passwords, API keys, or private keys
- Reference vault variables with a `vault_` prefix in variable names

## Quality Tools

- **ansible-lint** for Ansible-specific linting
- **yamllint** for YAML syntax and style checking
- **molecule** for role testing
