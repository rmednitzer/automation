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
├── playbooks/             # site-common, sre-toolchain, local-inference, redfish-oob
├── roles/<role>/
│   ├── defaults/main.yml  # Default variables (overridable)
│   ├── tasks/main.yml     # Main task list
│   ├── handlers/main.yml  # Handlers (if needed)
│   ├── templates/         # Role-scoped Jinja2 templates
│   ├── files/             # Role-scoped static files
│   ├── meta/main.yml      # Role metadata (Galaxy info, dependencies)
│   └── README.md          # Role documentation
├── group_vars/all.yml     # Global group variables
├── docs/                  # ADRs, compliance-controls.yml, schemas/, examples/
└── scripts/               # validate-compliance-controls.py
```

Add custom plugins under `plugins/{filter,lookup,modules}/` only when
one is needed, and configure the matching plugin path in `ansible.cfg`.
Do not pre-create empty plugin directories.

## Current state

- A compliance-aligned hardening baseline of 19 roles applied to fleet
  hosts by `playbooks/site-common.yml`: `common`, `apparmor`,
  `kernel_lockdown`, `usbguard`, `users`, `ntp`, `dns`, `ssh_hardening`,
  `ufw`, `nftables_egress`, `fail2ban`, `aide`, `rkhunter`, `auditd`,
  `log_forwarding`, `rsyslog_hardening`, `systemd_hardening` — plus
  `vector` and `wazuh_agent`, which stay **opt-in** (each needs a SIEM /
  manager endpoint, so the default baseline run is unaffected).
- Three roles live outside the baseline, each driven by its own playbook:
  `sre_toolchain` (`sre-toolchain.yml`) installs pinned-to-latest
  SRE/Platform/Security binaries from upstream GitHub releases with SHA256
  verification (operator hosts only — workstations, admin/bastion VMs, CI
  runners); `ollama` (`local-inference.yml`) provisions a local inference
  runtime; `redfish` (`redfish-oob.yml`) manages out-of-band BMC/Redfish
  configuration.
- **22 roles** and **4 playbooks** in total.

Target OS: Ubuntu 24.04 LTS (Noble) and Ubuntu 26.04 LTS (Resolute,
kernel 7.0). Each role's `meta/main.yml` declares both `noble` and
`resolute`. No official CIS 26.04 benchmark exists yet, so the 26.04
baseline is "CIS 24.04 + kernel-7.0/KSPP delta" — see
[`docs/ADR-004-ubuntu-2604-dual-support.md`](docs/ADR-004-ubuntu-2604-dual-support.md).

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

Two files demonstrate the convention:

- **Plaintext template** —
  [`inventories/development/group_vars/vault.yml.example`](inventories/development/group_vars/vault.yml.example):
  the placeholder structure, committed as-is (the `.example` suffix exempts
  it from the encryption guard). It stays in the inventory so contributors
  see where a real `vault.yml` would live.
- **Real encrypted file** —
  [`docs/examples/vault.yml`](docs/examples/vault.yml): an *actually*
  `ansible-vault`-encrypted `vault.yml` committed in encrypted form, so the
  `ansible-vault-encrypted` pre-commit guard
  (`scripts/check-vault-encrypted.sh`) has a real file to pass over and
  contributors see the end state. It lives under `docs/examples/`
  **deliberately outside any `inventories/<env>/group_vars/` path**: an
  encrypted `group_vars/vault.yml` auto-loads for every playbook run against
  that inventory, so a worked example sitting there would force ordinary
  development runs to supply the vault password. Parked under `docs/examples/`
  it never auto-loads, so `ansible-playbook -i inventories/development/hosts …`
  needs no vault password. Its throwaway password is **`example`**, documented
  in a comment inside the decrypted payload — it protects only placeholder
  values, never real secrets. The `**/vault.yml` lint globs and the
  `vault.yml` pre-commit guard both still cover it by filename. CI re-proves
  it decrypts (`vault-example` job in `.github/workflows/ci.yml`). View it
  with:

  ```bash
  ansible-vault view docs/examples/vault.yml
  # password: example
  ```

To bootstrap a real environment, copy the template, fill in real values,
then encrypt with a strong password (never documented):

```bash
cp inventories/development/group_vars/vault.yml.example \
   inventories/<env>/group_vars/vault.yml
# ... fill in real values ...
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
- **molecule** (role testing — `molecule/default` scenarios for `users`,
  `ssh_hardening`, `auditd`, `common`; run on-demand via the CI
  `workflow_dispatch` matrix since they need systemd-in-Docker, see
  LIMITATIONS L2)

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
