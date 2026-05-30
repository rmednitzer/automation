# `kernel_lockdown` role

Audits the **kernel lockdown LSM** level and, opt-in, sets it
(`integrity` / `confidentiality`) via the GRUB kernel command line, on Ubuntu
24.04 / 26.04 LTS.

Kernel lockdown restricts even `root`/`CAP_SYS_ADMIN` from modifying or reading
the running kernel in ways that would undermine its integrity or leak its
memory — a base-layer protection beneath the per-service confinement of
`apparmor` and `systemd_hardening`.

## What it does

- **Audits** the current level by reading `/sys/kernel/security/lockdown`
  (e.g. `[none] integrity confidentiality`) — read-only.
- **Opt-in**, appends `lockdown=<level>` to the kernel command line via an
  `/etc/default/grub.d/99-lockdown.cfg` drop-in (composing onto
  `GRUB_CMDLINE_LINUX`, never editing `/etc/default/grub`), regenerates
  `grub.cfg`, and **flags that a reboot is required** — it does not reboot.

## Safe by default

- **Audit only until you opt in.** `kernel_lockdown_level` is empty by default,
  so a baseline run reads the current level and **does not touch the boot
  command line**.
- **Never reboots.** Setting a level regenerates `grub.cfg` and emits a
  reboot-required notice; activation happens on the next (operator-scheduled)
  reboot. The audit shows `current` vs `desired` so a pending change is visible.
- **Container-guest aware** (`kernel_lockdown_runtime_managed`): lockdown is a
  host-kernel property, so container *guests* skip management entirely (no
  bootloader, shared `/sys`); a container/LXC **host** is managed normally —
  same `ansible_virtualization_role == 'guest'` pattern as `auditd` / `dns` /
  `apparmor`.

## Choosing a level (read before opting in)

| Level | Protects | Known to break |
|-------|----------|----------------|
| `integrity` | unsigned module load, `kexec`, `/dev/mem`, raw MSR/PCI, hibernation image | loading **unsigned** out-of-tree / DKMS modules; `kexec_load` |
| `confidentiality` | integrity **plus** kernel-memory reads: `perf`, `kprobes`, `/dev/kmem` | hibernation; most kernel tracing / debugging (`perf`, eBPF profiling) |

Notes:
- Lockdown can only be **raised** at runtime, never lowered — lowering needs a
  reboot with the new cmdline.
- With **Secure Boot** enabled, many Ubuntu kernels already start at
  `lockdown=integrity` automatically; check the audit before assuming `none`.
- `integrity` is a safe baseline for most servers **if** all required
  out-of-tree modules are signed; validate in staging first.
- Assumes the **GRUB** bootloader (Ubuntu default). Hosts using `systemd-boot`
  must set the cmdline through their loader entries instead.

## Usage

```yaml
# inventories/<env>/group_vars/<group>.yml
kernel_lockdown_level: integrity   # or "confidentiality"; "" = audit only
```

Then reboot the host (on your schedule) to activate it. Clearing the value back
to `""` is **audit-only and read-only** — it leaves any existing drop-in in
place (so the role never removes a `99-lockdown.cfg` it may not own). To have
the role tear down *its own* drop-in when you clear the level, set
`kernel_lockdown_remove_dropin_when_empty: true`; lockdown is still only lowered
after the next reboot.

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `kernel_lockdown_enabled` | `true` | Master switch (audit only until a level is set) |
| `kernel_lockdown_level` | `""` | `""` (audit) / `integrity` / `confidentiality` |
| `kernel_lockdown_audit` | `true` | Report the current level (read-only) |
| `kernel_lockdown_remove_dropin_when_empty` | `false` | Allow an empty-level run to remove this role's drop-in (off → audit-only stays read-only) |
| `kernel_lockdown_manage_runtime` | `true` | Manage audit + cmdline (auto-off in container guests) |
| `kernel_lockdown_grub_dropin` | `/etc/default/grub.d/99-lockdown.cfg` | Managed GRUB drop-in path |

Full list in `defaults/main.yml`.

## Compliance

POL-004 (integrity & confidentiality of processing — lockdown protects kernel
integrity and, at `confidentiality`, kernel-memory disclosure). CRA Annex I
Part I, NIS2 Art 21.2(e), GDPR Art 5(1)(f) / Art 25, ISO 27001:2022 A.8.27.
