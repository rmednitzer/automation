# ADR-004: Ubuntu 24.04 + 26.04 dual-support

- **Status:** Accepted
- **Date:** 2026-05-30
- **Deciders:** automation maintainers
- **Supersedes:** none (revisits LIMITATIONS L1 "Ubuntu 24.04 LTS only")
- **Related work:** ADR-003 (CIS baseline extension); kernel-7.0 / KSPP
  sysctl review.

## Context

Ubuntu 26.04 LTS ("Resolute Raccoon") was released 2026-04-23, shipping the
final Linux **7.0** kernel. The fleet will run a mix of 24.04 (Noble, kernel
6.8) and 26.04 (Resolute, kernel 7.0) hosts during the migration window, so
the hardening baseline must apply cleanly and idempotently to **both** —
without weakening the 24.04 posture. LIMITATIONS **L1** previously scoped the
roles to 24.04 only; this ADR opens dual-support and records the interim
benchmark stance.

A complication: **there is no official CIS Ubuntu 26.04 Benchmark yet.** CIS
publishes a benchmark per LTS on a lag (the 24.04 benchmark is v1.0.0). Until
a 26.04 benchmark exists we cannot map controls to a 26.04-specific document.

## Decisions

### 1. Target OS matrix

The supported target OS is now **Ubuntu 24.04 LTS and Ubuntu 26.04 LTS**.
Every role's `meta/main.yml` `platforms` block declares both Ubuntu release
codenames under `versions`:

```yaml
platforms:
  - name: Ubuntu
    versions:
      - noble      # 24.04 LTS
      - resolute   # 26.04 LTS (kernel 7.0)
```

Older releases (22.04 / jammy and earlier) remain out of scope.

### 2. Interim benchmark stance (no official CIS 26.04 yet)

Until CIS publishes an Ubuntu 26.04 Benchmark, the 26.04 hardening baseline
is derived as:

> **CIS Ubuntu 24.04 Benchmark v1.0.0** (the existing basis, see ADR-003)
> **+ kernel-7.0 / KSPP deltas** validated against the Linux Kernel
> Self-Protection Project "Recommended Settings" and the upstream kernel
> sysctl documentation.

This is recorded explicitly so an auditor understands that 26.04 controls
inherit the 24.04 mapping plus a documented, source-cited delta — not an
unmapped guess. When the official CIS 26.04 Benchmark lands, re-validate and
supersede this ADR.

### 3. Kernel-7.0 / KSPP sysctl review (role `common`)

Reviewed `common_sysctl_settings` and `tasks/kernel_hardening.yml` against
KSPP and kernel-7.0 defaults. Changes (all overridable, none weaken 24.04):

- **New universally-present knobs** added to `common_sysctl_settings`
  (present on both 6.8 and 7.0):
  - `net.core.bpf_jit_harden=2` — harden the eBPF JIT (KSPP; CIS §1).
  - `fs.protected_fifos=2`, `fs.protected_regular=2` — close file-creation
    races in world-writable sticky dirs (KSPP).
  - `vm.unprivileged_userfaultfd=0` — remove a recurring use-after-free LPE
    primitive (KSPP).
- **New kernel-version-dependent knobs** in a separate, **path-gated** dict
  `common_sysctl_settings_optional`, applied only when the `/proc/sys` path
  exists so the baseline stays idempotent across the matrix:
  - `kernel.io_uring_disabled=1` — io_uring is a prominent LPE surface; the
    sysctl exists on kernel ≥ 6.6 (both 6.8 and 7.0). Hosts whose workloads
    need io_uring override to `0`.
  - `dev.tty.legacy_tiocsti=0` — block legacy TIOCSTI terminal injection.
    The sysctl **only exists** when the kernel is built with
    `CONFIG_LEGACY_TIOCSTI=y`; hardened kernels compile it out (TIOCSTI is
    then already disabled), so the key is skipped where its path is absent.
- **Existing hardcoded kernel-hardening sysctls made overridable** (same
  default values — no weakening): `kernel.kptr_restrict`,
  `kernel.dmesg_restrict`, `kernel.unprivileged_bpf_disabled`,
  `kernel.randomize_va_space`, `kernel.yama.ptrace_scope` now read from
  `common_kernel_*` defaults. `kernel.unprivileged_userns_clone` keeps its
  `failed_when: false` gate (a Debian/Ubuntu-only knob).

`ptrace_scope` stays at **2** (CIS Ubuntu 24.04; admin-only). KSPP
recommends 3 (block all PTRACE_ATTACH) but that breaks privileged
debuggers/tooling, so 3 is offered as an override rather than the default.

### 4. PAM / unattended-upgrades / package names re-validated against 26.04

- **`pam_faillock` via `pam-auth-update`** (ADR-003 H4) is unchanged on
  26.04: the `/usr/share/pam-configs/` profile mechanism is still the
  Debian/Ubuntu-sanctioned, idempotent path. No 26.04-specific change.
- **`unattended-upgrades` + `apt-listchanges`** package names are unchanged
  on 26.04; `roles/common/tasks/auto_updates.yml` applies as-is.
- No role currently branches on `ansible_distribution_version`; none is
  required for the two supported releases. If a future 26.04 point-release
  diverges (e.g. a renamed package), gate that single task by
  `ansible_distribution_version` rather than forking the role.

### 5. Molecule matrix covers both releases

The `users` Molecule scenario now declares **two** platforms — a 24.04 box
(`geerlingguy/docker-ubuntu2404-ansible`) and a 26.04 box
(`geerlingguy/docker-ubuntu2604-ansible`) — so converge + idempotence +
verify run on both. New scenarios for `ssh_hardening`, `auditd`, and
`common` (ADR/LIMITATIONS L2/L3) likewise pin both images. None could be
**executed** in the authoring environment (no Docker); the CI `molecule`
job stays `continue-on-error` until a green run on a Docker host
(LIMITATIONS L2).

## Consequences

- One baseline now targets two kernels. The path-gated optional sysctls and
  the existing `failed_when: false` gates keep a first converge clean on
  both 6.8 and 7.0; a knob absent on one kernel is skipped, never fatal.
- 26.04 controls are auditable today as "24.04 CIS + cited kernel-7.0/KSPP
  delta". This ADR must be re-validated and superseded once an official CIS
  Ubuntu 26.04 Benchmark is published.
- Operators who route traffic, run kexec/live-patching, perf-profile, or run
  io_uring/ptrace-dependent workloads override the documented `common_*`
  sysctl defaults (see `roles/common/defaults/main.yml`).
- The 26.04 Molecule legs are authored but unproven until run on Docker
  (LIMITATIONS L2/L3/L5).

## References

- Ubuntu 26.04 LTS ("Resolute Raccoon") release notes — final Linux 7.0
  kernel (Canonical, 2026-04-23).
- Linux Kernel Self-Protection Project — "Recommended Settings"
  (`kspp.github.io/Recommended_Settings.html`): `bpf_jit_harden`,
  `protected_fifos`/`protected_regular`, `unprivileged_userfaultfd`,
  `kptr_restrict`, `dmesg_restrict`, `ptrace_scope`, `kexec_load_disabled`,
  `ldisc_autoload`, `legacy_tiocsti`.
- Linux kernel sysctl docs — `kernel.io_uring_disabled`
  (`Documentation/admin-guide/sysctl/kernel.rst`), io_uring added 6.6.
- `CONFIG_LEGACY_TIOCSTI` — default of `dev.tty.legacy_tiocsti`; compiled
  out on hardened kernels.
- CIS Ubuntu Linux 24.04 LTS Benchmark v1.0.0 — §1 (kernel/sysctl) basis.
- `pam-auth-update(8)`, `pam_faillock(8)`; `unattended-upgrades(8)`.
- `docs/ADR-003-runtime-correctness-and-cis-baseline.md` — CIS baseline,
  pam_faillock mechanism.
- LIMITATIONS L1 (now opened), L2/L3/L5 (Molecule coverage).
