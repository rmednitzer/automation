# CLAUDE.md — `automation`

Ansible automation: fleet hardening, configuration management,
operator-host toolchain provisioning. EU and Austrian regulatory
alignment. Apache License 2.0.

The repository is intentionally tool-named, not function-named: it owns
everything Ansible does, including but not limited to hardening.
Companions: `infra` (OpenTofu), `runbooks` (ad-hoc operator scripts).

## Compliance alignment

Technical controls mapped to:

- **NIS2 Directive (EU 2022/2555)** — Art 20–23: risk management,
  incident handling, reporting
- **NISG 2026 (Austrian transposition)** — effective 2026-10-01
- **Cyber Resilience Act (EU 2024/2847)** — Annex I: secure-by-design
- **GDPR (EU 2016/679) / Austrian DSG** — Art 5, 25, 32: data
  protection by design
- **ISO/IEC 27001:2022** — Annex A controls

Controls and policies live in
[`docs/compliance-controls.yml`](docs/compliance-controls.yml):

- Control catalog: `CTL-001`, `CTL-002`, `CTL-003`
- ISMS policies: `POL-001`, `POL-002`, `POL-003`, `POL-004`, `POL-005`

When modifying roles, **preserve compliance cross-references** in
`defaults/main.yml` headers. When adding controls, map them to the
relevant regulatory articles and add definitions to
`docs/compliance-controls.yml`.

## Repository layout

Standard Ansible best-practices layout. Files and templates used by a
role live **inside** that role (`roles/<role>/files/`,
`roles/<role>/templates/`), not at the repository root — per the
[official sample setup](https://docs.ansible.com/ansible/latest/tips_tricks/sample_setup.html).

```
automation/
├── CLAUDE.md / README.md / CONTRIBUTING.md / LIMITATIONS.md / CHANGELOG.md
├── LICENSE / NOTICE       # Apache License 2.0
├── ansible.cfg
├── requirements.yml       # Galaxy collections
├── Makefile               # Local lint / syntax-check / validate-compliance
├── inventories/<env>/     # production, staging, development
│   ├── hosts              # Inventory definitions
│   ├── group_vars/        # Per-env group variables
│   └── host_vars/         # Per-env host-specific variables
├── playbooks/             # site-common, sre-toolchain
├── roles/<role>/
│   ├── defaults/main.yml  # Default variables (overridable)
│   ├── tasks/main.yml     # Main task list
│   ├── handlers/main.yml  # Handlers (if needed)
│   ├── templates/         # Role-scoped Jinja2 templates
│   ├── files/             # Role-scoped static files
│   ├── meta/main.yml      # Role metadata (Galaxy info, dependencies)
│   └── README.md          # Role documentation
├── group_vars/all.yml     # Global group variables
├── docs/                  # ADR-001, compliance-controls.yml
└── scripts/               # validate-compliance-controls.py
```

Add custom plugins under `plugins/{filter,lookup,modules}/` only when
one is needed, and configure the matching plugin path in `ansible.cfg`.
Do not pre-create empty plugin directories.

## Current state

- A compliance-aligned hardening baseline of 10 roles applied to all
  fleet hosts by `playbooks/site-common.yml`: `common`, `users`, `ntp`,
  `ssh_hardening`, `ufw`, `fail2ban`, `aide`, `rkhunter`,
  `log_forwarding`, `auditd`.
- An operator-host toolchain role (`sre_toolchain`) invoked by
  `playbooks/sre-toolchain.yml`, installing pinned-to-latest
  SRE/Platform/Security binaries from upstream GitHub releases with
  SHA256 verification. Not part of the hardening baseline — targets
  operator hosts only (workstations, admin/bastion VMs, CI runners).

Target OS: Ubuntu 24.04 LTS.

Periodic re-validation against known-good sources (CIS Ubuntu Benchmark,
BSI TR-02102-4, upstream OpenSSH / chrony / auditd / `pam_faillock` /
`pam_pwquality` manuals, Ansible production-profile lint rules). Latest
baseline:
[`docs/ADR-001-code-validation-baseline.md`](docs/ADR-001-code-validation-baseline.md).
New ADRs increment the number and follow the same shape (Status, Date,
Context, Decisions, Consequences, References).

## Naming

- **Roles**: lowercase with underscores (`nginx_proxy`,
  `postgresql_server`)
- **Playbooks**: lowercase with hyphens (`deploy-app.yml`)
- **Variables**: lowercase with underscores, prefixed by role name
  (`nginx_listen_port`, `postgres_max_connections`)
- **Files/Templates**: lowercase with hyphens or underscores
- **Inventory groups**: lowercase with underscores (`web_servers`,
  `db_servers`)
- **Tags**: lowercase with hyphens (`install-packages`,
  `configure-service`)

## YAML style

- `.yml` extension (not `.yaml`)
- 2-space indentation
- Always `true`/`false` for booleans (never `yes`/`no`)
- Quote strings that contain special YAML characters
- Start every YAML file with `---`
- Block style (`key: value`) over flow style (`{key: value}`)

## Ansible practice

- Name every task descriptively
- FQCNs for all modules (`ansible.builtin.copy`, not `copy`)
- Prefer `ansible.builtin.template` over `ansible.builtin.copy` for
  config files needing substitution
- `become: true` only when needed, never globally
- Secrets in `ansible-vault` encrypted files; never plaintext
- `ansible.builtin.import_tasks` for static includes,
  `ansible.builtin.include_tasks` for dynamic
- Handlers for service restart/reload triggered by config changes
- `changed_when` and `failed_when` on `shell` / `command` tasks for
  accurate reporting

## Role structure

Every role:

- `defaults/main.yml` — default variables (overridable)
- `tasks/main.yml` — main task list
- `handlers/main.yml` — handlers (if needed)
- `meta/main.yml` — metadata and dependencies
- `README.md` — role documentation

## Variable precedence

Prefer defining variables at these levels (lowest precedence to highest):

1. `roles/<role>/defaults/main.yml` — role defaults
2. `inventories/<env>/group_vars/` — group-specific overrides
3. `inventories/<env>/host_vars/` — host-specific overrides
4. Playbook `vars:` — playbook-level overrides (use sparingly)

## Secrets management

Secrets live in `ansible-vault` encrypted files, never in plaintext.

### File and variable naming

- Vault-encrypted files are named `vault.yml`:
  `inventories/<env>/group_vars/vault.yml`,
  `inventories/<env>/host_vars/<host>/vault.yml`. These files are
  committed, but only in `ansible-vault`-encrypted form. The
  `ansible-vault-encrypted` pre-commit hook
  (`scripts/check-vault-encrypted.sh`) refuses any `vault.yml` whose first
  line is not the `$ANSIBLE_VAULT` header, so a plaintext secrets file
  cannot be committed by accident. Plaintext `vault.yml.example` templates
  are placeholders and are committed as-is.
  The reviewer signal is the `vault_` prefix on the *variables* (below),
  not the filename.
- Variables inside vault files use a `vault_` prefix
  (`vault_smtp_password`, `vault_sre_toolchain_github_token`). A
  non-vault file in the same `group_vars/` references them by aliasing:
  `smtp_password: "{{ vault_smtp_password }}"`. This keeps vault lookups
  out of role logic and makes the dependency explicit.

### Vault password source

Pick one of the three canonical sources, in order of preference:

1. **File pointed to by `ANSIBLE_VAULT_PASSWORD_FILE`** (operator
   workstation, CI). The file lives outside the repository, mode `0600`.
2. **`--vault-password-file <path>` on the CLI** for one-off runs.
3. **`vault_password_file = <path>` in `ansible.cfg`** only when the
   path is non-sensitive (for example, a developer-only shared file in a
   pair-programming context).

`ansible-vault` also supports `--ask-vault-pass` for interactive use; do
not script it.

### Worked example

See
[`inventories/development/group_vars/vault.yml.example`](../inventories/development/group_vars/vault.yml.example)
for the placeholder structure. Copy it to
`inventories/<env>/group_vars/vault.yml`, fill in real values, then
encrypt:

```bash
ansible-vault encrypt inventories/<env>/group_vars/vault.yml
```

Subsequent edits use `ansible-vault edit <path>`, which decrypts in a
temp buffer and re-encrypts on save.

### Hard rules

- Never commit unencrypted secrets, passwords, API keys, or private keys.
- Never commit the vault password file itself.
- Vault variables are referenced through `vault_`-prefixed names so a
  reviewer scanning a diff for plaintext credentials can trust the
  convention.

## Common commands

```bash
# Syntax check
ansible-playbook playbooks/<playbook>.yml --syntax-check

# Dry-run
ansible-playbook -i inventories/<env>/hosts playbooks/<playbook>.yml --check --diff

# Apply
ansible-playbook -i inventories/<env>/hosts playbooks/<playbook>.yml

# Tag filter
ansible-playbook -i inventories/<env>/hosts playbooks/<playbook>.yml --tags "tag1,tag2"

# Lint
ansible-lint
yamllint .

# Galaxy install
ansible-galaxy install -r requirements.yml

# Vault
ansible-vault encrypt <file>
ansible-vault view <file>
```

## Quality tools

- **ansible-lint** (production profile, FQCN + `no-changed-when`
  enforced)
- **yamllint** (project overrides in `.yamllint`)
- **molecule** (role testing — placeholder, see LIMITATIONS L2)

## Workflow

- Branch from `main` (`feature/add-nginx-role`,
  `fix/postgres-permissions`)
- Imperative commit subjects; explain the *why*
- One logical change per commit

## Notes for AI assistants

- Read existing files before modifying them
- Never commit plaintext secrets or credentials
- For new roles, follow the role structure above
- Be careful about environment separation when editing inventory
- Prefer idempotent operations
- Test playbooks with `--check --diff` before real runs when possible
- Use FQCNs for all module references
- Preserve compliance cross-references when editing role
  `defaults/main.yml` headers; the matching role list in
  `docs/compliance-controls.yml` must stay in sync
