# `dns` role

DNS resolver hardening via **systemd-resolved** for Ubuntu 24.04 / 26.04 LTS:
DNSSEC validation, DNS-over-TLS, and disabled LLMNR / MulticastDNS.

## What it does

- Deploys a `/etc/systemd/resolved.conf.d/90-ansible.conf` drop-in (never
  edits the vendor `resolved.conf` in place) configuring:
  - **DNSSEC** response validation (`allow-downgrade` by default — validates
    where the chain supports it, tolerant of unsigned/broken zones).
  - **DNS-over-TLS** (`opportunistic` by default — encrypts to resolvers that
    support it, falls back to cleartext rather than hard-failing).
  - **LLMNR** and **MulticastDNS** disabled (local spoofing/poisoning surface).
  - Local caching stub resolver and `/etc/hosts` resolution.
- Optionally pins upstream/fallback resolvers (DoT `IP#servername` form so a
  strict DoT cert SNI can be validated).
- Repoints `/etc/resolv.conf` at the `systemd-resolved` stub (`127.0.0.53`) so
  the stub resolver is actually on the query path.

**Safe-by-default:** `dns_resolvers` is empty by default, so the role keeps the
DHCP/link-provided resolvers (it does **not** break internal / split-horizon
DNS on a fleet-wide apply) and only layers on the hardening. Pin upstreams per
environment via `dns_resolvers`.

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `dns_resolvers` | `[]` | Global upstream resolvers (`IP#servername`); empty = keep link/DHCP DNS |
| `dns_fallback_resolvers` | Quad9 + Cloudflare (DoT) | Last-resort resolvers (only when no link resolver works) |
| `dns_search_domains` | `[]` | Search domains for unqualified lookups |
| `dns_dnssec` | `allow-downgrade` | DNSSEC mode (`yes` / `no` / `allow-downgrade`) |
| `dns_over_tls` | `opportunistic` | DNS-over-TLS mode (`yes` / `no` / `opportunistic`) |
| `dns_disable_llmnr` | `true` | Disable LLMNR |
| `dns_disable_multicast_dns` | `true` | Disable MulticastDNS |
| `dns_cache` | `true` | Local caching stub resolver |
| `dns_read_etc_hosts` | `true` | Resolve names from `/etc/hosts` |
| `dns_manage_resolv_conf` | `true` | Symlink `/etc/resolv.conf` → resolved stub |
| `dns_manage_service` | `true` | Enable/restart `systemd-resolved` (auto-off in container guests) |

Full list in `defaults/main.yml`.

## Notes

- **Containers.** In a container *guest* (`ansible_virtualization_role ==
  'guest'`) the service start/restart and the `resolv.conf` symlink are
  skipped (`dns_runtime_managed`), since `systemd-resolved` is usually not the
  resolver there and a restart can fail; the drop-in is still deployed so the
  config-as-code can be verified. A container/LXC **host** is managed normally.
- **Strict DoT (`dns_over_tls: "yes"`)** requires every configured resolver to
  present a certificate matching its `#servername` SNI — confirm your
  resolvers are DoT-correct before enabling, or resolution will fail.
- **Strict DNSSEC (`dns_dnssec: "yes"`)** returns SERVFAIL for zones that fail
  validation (including some misconfigured-but-reachable zones); the default
  `allow-downgrade` avoids breaking those.

## Compliance

POL-003 (cryptography — DoT transport + DNSSEC authenticity), NIS2 Art 21.2(e)
(network security), CRA Annex I (attack-surface minimisation), GDPR Art 32
(confidentiality of processing), ISO 27001:2022 A.8.24.
