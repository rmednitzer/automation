# `apparmor` role

Ensures **AppArmor** — Ubuntu's default Mandatory Access Control (MAC) LSM — is
installed and active, audits profile coverage, and (opt-in) moves named
profiles into complain/enforce mode, on Ubuntu 24.04 / 26.04 LTS.

## What it does

- Installs `apparmor` + `apparmor-utils` (and, by default, the
  `apparmor-profiles` / `apparmor-profiles-extra` sets from *universe*).
- Enables and starts the `apparmor` service.
- **Audits** profile coverage by parsing `aa-status --json` — reports the
  enforce / complain / loaded counts (read-only).
- **Opt-in** moves the profiles you list into complain or enforce mode,
  idempotently (only profiles that are loaded and not already in the target
  mode are touched).

## Safe by default

- **No profile mode is changed unless you opt it in.**
  `apparmor_enforce_profiles` / `apparmor_complain_profiles` are empty by
  default, so a baseline run only ensures AppArmor is active and audits it —
  it will not flip a profile to enforce and risk breaking the confined program.
- **Container-guest aware** (`apparmor_runtime_managed`): in a container
  *guest* the service management, profile changes and audit are skipped
  (AppArmor policy is the host kernel's responsibility there and apparmorfs is
  not writable) while packages are still installed; a container/LXC **host** is
  managed normally — the same `ansible_virtualization_role == 'guest'` pattern
  as `auditd` / `dns`.

## Usage

Triage a profile in complain mode (denials are logged, not blocked), confirm
the app still works and the logs are clean, then promote it to enforce:

```yaml
# inventories/<env>/group_vars/<group>.yml
# Use a TOP-LEVEL profile name / executable path as listed by `aa-status`
# (e.g. /usr/sbin/tcpdump). Child/hat profiles (names containing `//`) are not
# valid arguments to aa-enforce/aa-complain and are rejected with guidance.
# Check current names with: sudo aa-status
apparmor_complain_profiles:
  - /usr/sbin/tcpdump
apparmor_enforce_profiles:
  - /usr/bin/man
  - /usr/sbin/nscd
```

The role only acts on profiles that are **loaded** (present in `aa-status`) and
not already in the requested mode, so re-runs are no-ops and a mistyped /
unloaded profile name is skipped rather than erroring; `changed_when` reflects
the tool actually transitioning the profile, so a no-op is never reported as a
change. Profiles installed by the package step are **reloaded before the
audit** (a changed package set notifies the `Reload AppArmor` handler, flushed
ahead of `aa-status`) so the audit and mode changes see the current profile
set, not a stale one.

### Disabled AppArmor is a failure, not a skip

On a managed (non-container) host where the AppArmor LSM is **not active**
(no `/sys/kernel/security/apparmor` — disabled at the kernel cmdline or
securityfs not mounted), the role **fails** with remediation guidance rather
than silently continuing — a MAC-enforcement role should not let a hardening
run pass while MAC is off. The active check (apparmorfs) runs **before** any
profile reload, so a disabled host is diagnosed cleanly rather than failing on
a reload of the inactive service. Set `apparmor_require_enabled: false` for
hosts that legitimately run without AppArmor.

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `apparmor_enabled` | `true` | Master switch (enable + audit only until profiles opted in) |
| `apparmor_packages` | `apparmor`, `apparmor-utils` | Core LSM userspace + tools |
| `apparmor_install_extra_profiles` | `true` | Install `apparmor-profiles` + `-profiles-extra` |
| `apparmor_complain_profiles` | `[]` | Profiles to set to complain (log-only) mode |
| `apparmor_enforce_profiles` | `[]` | Profiles to set to enforce mode |
| `apparmor_audit` | `true` | Report enforce/complain/loaded counts (read-only) |
| `apparmor_require_enabled` | `true` | Fail on a managed host if AppArmor proves to be disabled |
| `apparmor_manage_runtime` | `true` | Manage service/profiles/audit (auto-off in container guests) |

Full list in `defaults/main.yml`.

## Notes

- AppArmor is shipped and enabled by default on Ubuntu; this role makes that
  state explicit and auditable, and gives a controlled path to enforce
  additional profiles. It does **not** ship custom profiles — add those under
  `/etc/apparmor.d/` (a future enhancement can template role-specific
  profiles).
- `apparmor-profiles-extra` is in the *universe* component (enabled by default
  on Ubuntu). Set `apparmor_install_extra_profiles: false` on images without
  universe.

## Compliance

POL-001 (access control — AppArmor is Mandatory Access Control: program-level
information access restriction complementing the user-level controls). CRA
Annex I Part I, NIS2 Art 21.2(e), GDPR Art 25 / Art 5(1)(f),
ISO 27001:2022 A.8.3 / A.5.15.
