# `vector` role

Installs and configures **[Vector](https://vector.dev)** (by Datadog) as a
modern log shipper — reads the systemd journal and ships to a SIEM sink — on
Ubuntu 24.04 / 26.04 LTS.

Vector is the modern complement to the rsyslog-based `log_forwarding` role: use
Vector as the **shipper** (structured, buffered, many sink types) and let
rsyslog handle **local** logging. Pick one shipper per log path — don't double-
ship the same source to the same SIEM from both roles.

## What it does

- Adds the Vector APT repository with a `signed-by` Datadog keyring (packages
  are verified against the imported signing keys); imports the documented
  Datadog key **set** (current + rollover, so rotation doesn't break apt) and
  optionally **pins** the allowed fingerprints (`vector_apt_key_fingerprints`).
- Installs `vector` (version-pinnable).
- Deploys `/etc/vector/vector.yaml` from `vector_sources` / `vector_transforms`
  / `vector_sinks`, validated with `vector validate` before it is placed.
- Enables and starts the `vector` service.

## Enablement & secrets

- **Off by default** (`vector_enabled: false`); `playbooks/site-common.yml` runs
  the role only when enabled. Turn it on per environment once a SIEM sink is
  defined.
- `vector_sinks` is **required** when enabled (there is no safe default
  destination — the role asserts it). Define where logs go in `group_vars`.
- A sink secret (HEC token, API key) is a **secret** — never hardcode it.
  Reference a vault variable:

  ```yaml
  # inventories/<env>/group_vars/<group>.yml
  vector_enabled: true
  vector_sinks:
    siem:
      type: splunk_hec_logs
      inputs: ["journal"]
      endpoint: "https://splunk.example.internal:8088"
      default_token: "{{ vault_vector_splunk_hec_token }}"
  ```

  Or syslog-over-TLS to a generic SIEM:

  ```yaml
  vector_sinks:
    siem:
      type: socket
      inputs: ["journal"]
      mode: tcp
      address: "siem.example.internal:6514"
      encoding: { codec: "syslog" }
      tls: { enabled: true, verify_certificate: true }
  ```

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `vector_enabled` | `false` | Gate in `site-common.yml` |
| `vector_sources` | `journal` (journald) | Vector sources (component → config) |
| `vector_transforms` | `{}` | Optional Vector transforms |
| `vector_sinks` | `{}` | **Required when enabled** — where logs go (use a vault var for secrets) |
| `vector_version` | `""` (latest) | Pin a package version, e.g. `0.40.0-1` |
| `vector_apt_key_fingerprints` | `[]` | Optional supply-chain pin — allowed key fingerprints (verified when set) |
| `vector_manage_service` | `true` | Manage the service (auto-off in container guests) |

Full list in `defaults/main.yml`.

## Notes

- **Containers.** In a container *guest* the service start/restart is skipped
  (`vector_runtime_managed`) while the repo + config are still applied; a
  container/LXC **host** is managed normally (same
  `ansible_virtualization_role == 'guest'` pattern as `auditd` / `wazuh_agent`).
- **vs. `log_forwarding`.** `log_forwarding` ships via rsyslog/audisp-remote;
  this role ships via Vector. They can coexist (e.g. Vector for journald,
  audisp-remote for the kernel audit stream) but avoid sending the same records
  to the same collector twice.

## Compliance

CTL-002 (evidence store — host logs to the SIEM), CTL-003 (centralised logging /
forensic correlation, TLS in transit), POL-003 (crypto/TLS). NIS2 Art 21.2(a)(b),
GDPR Art 5(2) / Art 32, ISO 27001:2022 A.8.15 / A.8.16.
