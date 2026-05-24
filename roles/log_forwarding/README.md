# Log Forwarding Role

Centralised log forwarding via rsyslog (syslog) and `audisp-remote`
(auditd) for Ubuntu 24.04 LTS.

## What it does

- Installs and configures `rsyslog` for remote forwarding
- Supports `tcp`, `udp`, and `relp` (reliable event-passing) transports
- Optional TLS encryption for syslog transport via `rsyslog-gnutls`
  (POL-003)
- Forwards audit events directly via `audisp-remote` on the
  Ubuntu 24.04 `/etc/audit/plugins.d/` path, with the destination
  declared in `/etc/audit/audisp-remote.conf` (without that file the
  plugin sends events nowhere)
- Configures the rsyslog action queue (`LinkedList`, depth 10 000) so
  events survive a SIEM outage
- Applies a rate limit on the rsyslog action to bound spike-driven
  bandwidth (GDPR Art 5(1)(c) data minimisation)
- Skips all forwarding deploy steps when `log_forwarding_server` is
  empty, so an un-configured host stays quiet rather than failing

## Key Variables

| Variable                              | Default       | Description |
|---------------------------------------|---------------|-------------|
| `log_forwarding_enabled`              | `true`        | Master enable switch |
| `log_forwarding_protocol`             | `tcp`         | Syslog transport: `tcp`, `udp`, or `relp` |
| `log_forwarding_server`               | `""`          | Remote SIEM / aggregator endpoint (forwarding is a no-op while empty) |
| `log_forwarding_port`                 | `514`         | Remote syslog port |
| `log_forwarding_tls_enabled`          | `false`       | Wrap syslog forwarding in TLS (`gtls`) |
| `log_forwarding_tls_ca_cert`          | `""`          | CA cert path (server validation) |
| `log_forwarding_tls_cert`             | `""`          | Client cert path (optional mutual TLS) |
| `log_forwarding_tls_key`              | `""`          | Client key path (optional mutual TLS) |
| `log_forwarding_audit`                | `true`        | Forward auditd events via `audisp-remote` |
| `log_forwarding_audit_port`           | `60`          | `audisp-remote` destination port |
| `log_forwarding_audit_transport`      | `tcp`         | `audisp-remote` transport (`tcp` or `krb5`) |
| `log_forwarding_queue_size`           | `10000`       | rsyslog / audisp queue depth |
| `log_forwarding_queue_type`           | `LinkedList`  | rsyslog queue type |
| `log_forwarding_rate_limit_interval`  | `5`           | Rate-limit window (seconds) |
| `log_forwarding_rate_limit_burst`     | `200`         | Events per window |

See `defaults/main.yml` for the full list.
