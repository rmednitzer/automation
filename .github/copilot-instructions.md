# Copilot Instructions — `automation`

Ansible automation: fleet hardening, configuration management,
operator-host toolchain. Companions: `infra` (OpenTofu), `runbooks`
(ad-hoc operator scripts). Full conventions live in `CLAUDE.md`; this
file is the short form.

## Repository layout

Standard Ansible best-practices layout with `inventories/<env>/`
(production, staging, development, each with their own `group_vars/`
and `host_vars/`), `playbooks/`, `roles/`, and a global
`group_vars/all.yml`. Files and templates live inside each role
(`roles/<role>/files/`, `roles/<role>/templates/`) — there is no
top-level `files/`, `templates/`, `host_vars/`, or `plugins/`
directory. Plugin subdirectories are created on demand alongside the
matching `ansible.cfg` plugin-path setting. See `CLAUDE.md` for the
full structure.

## Naming

- **Roles**: lowercase with underscores (`nginx_proxy`,
  `postgresql_server`)
- **Playbooks**: lowercase with hyphens (`deploy-app.yml`)
- **Variables**: lowercase with underscores, prefixed by role name
- **Files/Templates**: lowercase with hyphens or underscores
- **Inventory groups**: lowercase with underscores (`web_servers`)
- **Tags**: lowercase with hyphens (`install-packages`)

## YAML style

- `.yml` extension (not `.yaml`)
- 2-space indentation
- `true`/`false` for booleans (never `yes`/`no`)
- Quote strings containing special YAML characters
- Start every YAML file with `---`
- Block style (`key: value`) over flow style

## Ansible practice

- Name every task descriptively
- FQCNs for all modules (`ansible.builtin.copy`, not `copy`)
- Prefer `ansible.builtin.template` over `ansible.builtin.copy` for
  config files needing substitution
- `become: true` only when needed, never globally
- Secrets in `ansible-vault` encrypted files; never plaintext
- `ansible.builtin.import_tasks` for static, `include_tasks` for dynamic
- Handlers for service restart/reload from config changes
- `changed_when` and `failed_when` on `shell`/`command` tasks
- Prefer idempotent operations

## Role structure

Every role:

- `defaults/main.yml` — default variables (overridable)
- `tasks/main.yml` — main task list
- `handlers/main.yml` — handlers (if needed)
- `meta/main.yml` — metadata and dependencies
- `README.md` — role documentation

## Variable precedence

1. `roles/<role>/defaults/main.yml` (lowest)
2. `inventories/<env>/group_vars/`
3. `inventories/<env>/host_vars/`
4. Playbook `vars:` (use sparingly)

## Secrets

- `ansible-vault` for sensitive data
- Vault files: `vault_` prefix
- Never commit unencrypted secrets, passwords, API keys, or private keys
- Reference vault variables with a `vault_` prefix in variable names

## Quality tools

- **ansible-lint** (production profile, FQCN + `no-changed-when`
  enforced)
- **yamllint** (project overrides in `.yamllint`)
- **molecule** (role testing — placeholder; see LIMITATIONS L2)
