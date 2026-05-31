# ADR-005: Out-of-band management via Redfish

- **Status:** Proposed (aspirational — no BMC hardware in the fleet yet)
- **Date:** 2026-05-31
- **Deciders:** automation maintainers
- **Supersedes:** none
- **Related work:** ADR-002 (supply-chain verification); POL-001 (access
  control); the `redfish` role and `playbooks/redfish-oob.yml`.

## Context

The fleet today is consumer/prosumer hardware (workstations, a laptop) with no
dedicated baseboard management controllers (BMCs). As it grows toward
rack-mounted servers, those will ship BMCs — Dell iDRAC, HPE iLO, Lenovo XCC,
or OpenBMC — exposing **out-of-band (OOB)** management: power control, firmware
inventory and update, BIOS/UEFI settings, boot order, sensors, and the system
event log, all reachable independently of the host OS.

A BMC is the **single most privileged access path to a machine**: it has
pre-boot, persistent, below-the-OS control, it runs its own (often slow-to-be-
patched) firmware stack, and historically BMCs/IPMI have been a rich source of
critical vulnerabilities. Bringing OOB online without a security-first design
would add the fleet's most dangerous attack surface by default.

We want the management approach **decided and codified before the hardware
arrives**, so the first BMC is onboarded into a vetted pattern rather than an
ad-hoc one. Two broad options exist for the interface:

- **IPMI** — legacy, widely deprecated, weak crypto, per-vendor quirks.
- **Redfish** — the DMTF standard (DSP0266): a vendor-neutral HTTPS/JSON REST
  API, now supported by all major BMC vendors and by Ansible's
  `community.general.redfish_*` modules (already pinned in `requirements.yml`).

## Decisions

### 1. Redfish is the OOB management interface

Standardise on **Redfish**, driven from the control/bastion host via
`community.general.redfish_info` / `redfish_command` / `redfish_config`. IPMI-
over-LAN is to be **disabled** on BMCs where Redfish is available. Rationale:
one vendor-neutral, TLS-secured, scriptable, auditable interface instead of
per-vendor tooling or legacy IPMI.

### 2. Network isolation is mandatory

BMCs live on a **dedicated, isolated management network/VLAN**, never on a
production or internet-facing segment, reachable **only** from the
bastion/management host. This is the primary control: a BMC compromise requires
first reaching the management plane. (Enforced in `infra` networking, not this
role — recorded here as the governing constraint.)

### 3. Security-first defaults

- **Off by default.** The `redfish` role and its playbook ship inert
  (`redfish_enabled: false`, empty `redfish_bmcs`); nothing runs until BMC
  endpoints are explicitly defined.
- **Read-first.** The default action is read-only inventory (systems, firmware,
  thermals). State-changing operations (power) are **hard-gated** behind both
  an explicit `redfish_action: power` *and* `redfish_confirm_state_change: true`,
  so a stray variable can never cycle a machine's power.
- **TLS verification on** (`validate_certs: true`); loosened only for a lab BMC
  with an out-of-band-pinned self-signed certificate.
- **Strong, unique, vaulted credentials** per BMC (`vault_`-prefixed), never
  committed; default BMC accounts are removed/renamed.
- **No secrets in logs** — credential-bearing tasks use `no_log: true`.
- **Audited.** OOB actions run from the bastion and are logged centrally
  (log_forwarding / vector), satisfying POL-001 accountability.

### 4. Firmware resiliency posture (NIST SP 800-193)

BMC and platform firmware are tracked via Redfish firmware inventory and kept
patched; firmware updates are applied through Redfish with verified images.
This makes firmware a first-class, inventoried, patchable asset (CRA Annex I).

## Consequences

- **Forward-ready, inert today.** The capability is reviewed and committed; it
  does nothing until BMCs exist, so it adds no attack surface now.
- **Clear onboarding path.** Adding a server means: place its BMC on the
  management VLAN, vault its credentials, add it to `redfish_bmcs`, run
  `playbooks/redfish-oob.yml` for inventory.
- **Compliance.** Mapped to POL-001 (privileged access control); supports CRA
  Annex I (secure management/firmware) and NIS2 Art 21.2(d)(e).
- **Scope.** This ADR + role cover the management *pattern* and read/power
  operations. BIOS/boot configuration, firmware update workflows, and BMC user
  provisioning are deferred to follow-up work when real hardware exists.

## References

- DMTF Redfish Specification (DSP0266) and Schema (DSP8010).
- NIST SP 800-193 — Platform Firmware Resiliency Guidelines.
- CIS / vendor BMC hardening guidance (iDRAC, iLO, XCC, OpenBMC).
- `community.general` Redfish modules (`redfish_info`, `redfish_command`,
  `redfish_config`).
- ISO/IEC 27001:2022 A.8.2 (privileged access rights), A.8.9 (configuration
  management).
