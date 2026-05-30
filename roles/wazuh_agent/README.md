# `wazuh_agent` role

Installs and enrols the **Wazuh agent** (host-based intrusion detection, file
integrity monitoring, rootcheck) reporting to a Wazuh manager, on Ubuntu
24.04 / 26.04 LTS.

## What it does

- Adds the Wazuh 4.x APT repository with a `signed-by` keyring (packages are
  verified against the imported signing key); optionally **pins and verifies**
  the key fingerprint (`wazuh_apt_key_fingerprint`).
- Installs `wazuh-agent` (version-pinnable).
- Deploys `/var/ossec/etc/ossec.conf`: manager connection, auto-**enrollment**
  (authd), **syscheck** (FIM) on `/etc`, `/usr/bin`, `/boot`, … (realtime on
  `/etc`), **rootcheck**, journald + auth/dpkg log collection, active response.
- Deploys the enrollment password to `/var/ossec/etc/authd.pass` (when set),
  with `no_log` so the secret never reaches the Ansible log.
- Enables and starts the `wazuh-agent` service.

## Enablement & secrets

- **Off by default** (`wazuh_agent_enabled: false`); `playbooks/site-common.yml`
  runs the role only when enabled. Turn it on per environment once a manager
  exists.
- `wazuh_manager_address` (an IP/host, non-secret) is **required** — set it in
  `group_vars`. The role asserts it.
- The enrollment password is a **secret** — never hardcode it. Reference a
  vault variable:

  ```yaml
  # inventories/<env>/group_vars/<group>.yml
  wazuh_agent_enabled: true
  wazuh_manager_address: "wazuh.example.internal"
  wazuh_registration_password: "{{ vault_wazuh_registration_password }}"
  ```

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `wazuh_agent_enabled` | `false` | Gate in `site-common.yml` |
| `wazuh_manager_address` | `""` | Manager IP/host (**required**) |
| `wazuh_manager_port` | `1514` | Agent→manager reporting port |
| `wazuh_registration_address` | `""` | authd endpoint (defaults to the manager) |
| `wazuh_registration_port` | `1515` | authd port |
| `wazuh_registration_password` | `""` | Enrollment secret (**use a vault var**) |
| `wazuh_agent_name` | `{{ inventory_hostname }}` | Registered agent name |
| `wazuh_agent_groups` | `default` | Agent group(s) |
| `wazuh_agent_version` | `""` (latest) | Pin a package version, e.g. `4.9.2-1` |
| `wazuh_apt_key_fingerprint` | `""` | Optional supply-chain pin (verified when set) |
| `wazuh_fim_directories` | `/etc` (realtime), `/usr/bin`, `/usr/sbin`, `/bin`, `/sbin`, `/boot` | FIM watch list |
| `wazuh_manage_service` | `true` | Manage the service (auto-off in container guests) |

Full list in `defaults/main.yml`.

## Notes

- **Containers.** In a container *guest* the service start/restart is skipped
  (`wazuh_runtime_managed`) — FIM realtime/audit hooks are limited there — while
  the repo + config are still applied. A container/LXC **host** is managed
  normally (same `ansible_virtualization_role == 'guest'` pattern as `auditd` /
  `dns`).
- **Testing** needs a reachable manager and outbound HTTPS to
  `packages.wazuh.com`; run against a lab manager rather than in plain PR CI.

## Compliance

CTL-002 (HIDS/FIM/rootcheck as forensic evidence), POL-002 (automated
detection / incident response), NIS2 Art 21.2(a)(b) + Art 23, GDPR Art 5(2),
ISO 27001:2022 A.8.15 / A.8.16.
