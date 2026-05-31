# `redfish` role

**Aspirational** out-of-band (BMC) management via the [Redfish](https://www.dmtf.org/standards/redfish)
API. Driven from the control/bastion host against BMC endpoints (Dell iDRAC, HPE
iLO, Lenovo XCC, OpenBMC, …). See **[`docs/ADR-005`](../../docs/ADR-005-out-of-band-redfish.md)**
for the strategy and security rationale.

> The current fleet has **no enterprise BMCs**, so this role ships **inert**
> (`redfish_enabled: false`, empty `redfish_bmcs`). It's committed now so the
> first server is onboarded into a vetted, security-first pattern rather than an
> ad-hoc one.

## What it does

Run via [`playbooks/redfish-oob.yml`](../../playbooks/redfish-oob.yml) from the
control host (`delegate_to: localhost`):

- **`inventory`** (default, read-only) — collects system, firmware and thermal
  inventory from each BMC via `community.general.redfish_info`.
- **`power`** (hard-gated) — changes power state via
  `community.general.redfish_command`, but only when **both**
  `redfish_action: power` **and** `redfish_confirm_state_change: true` are set.

## Security model (POL-001 / ADR-005)

- **Off by default**; nothing runs until `redfish_bmcs` is populated.
- **Read-first**; power is double-gated so a stray variable can't cycle a host.
- **TLS verification on** (`redfish_validate_certs: true`).
- **Vaulted, unique per-BMC credentials** (`vault_`-prefixed) — never committed.
- **`no_log: true`** on credential-bearing tasks.
- BMCs belong on an **isolated management VLAN** reachable only from the bastion
  (enforced in `infra`, not this role — see ADR-005 §2).

## Usage

```yaml
# inventories/<env>/group_vars/bmc.yml  (password from vault.yml)
redfish_bmcs:
  - name: server01-bmc
    baseurl: "https://10.50.0.11"
    username: "automation"
    password: "{{ vault_redfish_server01_password }}"
```

```bash
# Read-only inventory:
ansible-playbook playbooks/redfish-oob.yml

# Power action (explicit, double-confirmed):
ansible-playbook playbooks/redfish-oob.yml \
  -e redfish_action=power -e redfish_power_command=GracefulRestart \
  -e redfish_confirm_state_change=true
```

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `redfish_enabled` | `false` | Master switch (the playbook sets it true) |
| `redfish_bmcs` | `[]` | BMC endpoints (name/baseurl/username/vaulted password) |
| `redfish_validate_certs` | `true` | Verify BMC TLS certificate |
| `redfish_action` | `inventory` | `inventory` (read) or `power` (hard-gated) |
| `redfish_confirm_state_change` | `false` | Must be true (with action=power) to change power |
| `redfish_power_command` | `GracefulRestart` | `On`/`ForceOff`/`GracefulShutdown`/`GracefulRestart`/`ForceRestart`/`Reboot` |

Requires the `community.general` collection (pinned in `requirements.yml`).

## Compliance

POL-001 (privileged out-of-band access control). CRA Annex I (secure
management/firmware), NIS2 Art 21.2(d)(e), ISO 27001:2022 A.8.2 / A.8.9, NIST SP
800-193 (firmware resiliency).
