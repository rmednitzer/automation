# `nftables_egress` role

Adds **default-deny outbound (egress) filtering** with an allow-list, using
nftables, on Ubuntu 24.04 / 26.04 LTS. ufw governs *ingress*; this role
constrains what a host may *initiate* — so a compromised host cannot freely
exfiltrate data or reach command-and-control.

## What it does

- Ensures `nftables` is installed.
- Deploys an egress policy in a **separate `inet fw_egress` table** that
  composes with ufw (ufw's ruleset is never modified), loaded at boot by a
  small `nftables-egress.service` unit.
- Runs the policy in one of three modes (`nftables_egress_mode`).

## Safe by default, and lock-out-safe

Egress-deny is the most disruptive control in this collection — a wrong rule
can cut a host off from DNS/updates or strand it. So:

- **A deliberate risk ladder, off by default.**
  - `off` (default) — deploys **nothing**; just ensures nftables is present. The
    fleet baseline is unaffected.
  - `observe` — loads the table with policy **ACCEPT** and **logs** every
    non-allow-listed new connection. Nothing is dropped; use it to discover the
    egress a host needs before enforcing.
  - `enforce` — policy **DROP**: only loop-back, established/related and the
    allow-list may leave the host.
- **Enforce cannot lock you out.** The chain *always* accepts `oif lo` and
  `ct state established,related`, so the return path of the inbound SSH /
  Ansible session (and any established connection) keeps working under enforce.
- **The ruleset is syntax-checked before it is applied** (`nft -c -f` via the
  template `validate:`), so a malformed table is never written or loaded.
- **Composes with ufw** — a separate table, idempotently replaced on reload
  (`table … ; delete table … ; table { … }`); ufw is untouched.
- **Container-guest aware** (`nftables_egress_runtime_managed`): egress
  filtering is a host network property, so container *guests* skip entirely; a
  container/LXC **host** is managed normally — same
  `ansible_virtualization_role == 'guest'` pattern as `kernel_lockdown` /
  `usbguard`.

> Roll out as `observe` first, review the `nft-egress-drop` journal entries,
> add what's missing to the allow-list, then move to `enforce` — ideally with
> out-of-band/console access the first time.

## Allow-list

`nftables_egress_allow` defaults cover core host functions so `enforce` does not
break them: DNS (53), NTP (123), HTTP/HTTPS (80/443, for apt/updates), DHCP
(67), plus ICMP/ICMPv6. Tighten or extend per environment; use
`nftables_egress_allow_extra` for destination-specific rules (raw nft
fragments), e.g. the SIEM collector or Wazuh manager:

```yaml
# inventories/<env>/group_vars/<group>.yml
nftables_egress_mode: observe        # then "enforce" once validated
nftables_egress_allow_extra:
  - 'ip daddr 10.20.0.10 tcp dport 514 accept comment "rsyslog SIEM"'
  - 'ip daddr 10.20.0.11 tcp dport 1514 accept comment "wazuh manager"'
```

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `nftables_egress_enabled` | `true` | Master switch |
| `nftables_egress_mode` | `off` | `off` / `observe` (log-only) / `enforce` (drop) |
| `nftables_egress_allow` | DNS, NTP, HTTP/HTTPS, DHCP | Allow-listed proto+dport (to any) |
| `nftables_egress_allow_extra` | `[]` | Raw nft rule fragments (destination-specific) |
| `nftables_egress_log_rate` | `10/minute` | Rate limit for the unmatched-egress log |
| `nftables_egress_manage_runtime` | `true` | Manage runtime (auto-off in container guests) |

Full list in `defaults/main.yml`.

## Compliance

POL-001 (access control — default-deny applied to outbound traffic, the network
complement to ufw's ingress control). CRA Annex I Part I, NIS2 Art 21.2(e),
GDPR Art 5(1)(f), ISO 27001:2022 A.8.20 / A.8.21.
