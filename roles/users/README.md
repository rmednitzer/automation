# `users` role

User management, sudo hardening, password policy, and account lockout
for Ubuntu 24.04 LTS.

## What it does

- Configures password aging and complexity via PAM (`pam_pwquality`)
  and `/etc/login.defs`
- Wires `pam_faillock` into the PAM stack the Debian-sanctioned way —
  shipping `/usr/share/pam-configs/faillock` and `…/faillock-notify`
  profiles and enabling them with `pam-auth-update --package --enable`,
  then asserting `pam_faillock.so` actually landed in the generated
  `common-auth`/`common-account` — and templates
  `/etc/security/faillock.conf` so the lockout policy is enforced
  (see the lockout-risk note below)
- Sets the stored-password hash to `YESCRYPT` (POL-003)
- Hardens sudo with full I/O logging, lecture, restricted
  `secure_path`, and `visudo -cf` validation on the deployed dropin
- Creates managed user accounts and deploys SSH keys via
  `ansible.posix.authorized_key`
- Sets restrictive home directory permissions (`0750`)
- Ships a single `/etc/profile.d/99-hardening.sh` drop-in for `umask`
  and a `readonly`+`export`ed shell login `TMOUT` (so it cannot be
  `unset`), instead of editing `/etc/profile` in place
- Sets `nologin` on unused system accounts
- Locks the root account by default (administrative access via sudo)

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `users_managed` | `[]` | Accounts to manage (`name`, `groups`, `shell`, `ssh_keys`, `state`) |
| `users_sudo_group` | `sudo` | Group granted sudo |
| `users_sudo_passwordless` | `false` | Allow passwordless sudo for `users_sudo_group` |
| `users_sudo_require_tty` | `false` | `Defaults requiretty` in sudoers (off so Ansible's no-TTY `become` keeps working — see defaults comment) |
| `users_password_max_days` | `90` | Password expiry (days) |
| `users_password_min_days` | `7` | Minimum days between password changes |
| `users_password_warn_days` | `14` | Warn before expiry (days) |
| `users_password_min_length` | `14` | Minimum password length (`pwquality` `minlen`) |
| `users_password_remember` | `12` | Password-history depth (`pam_unix remember=`) |
| `users_password_min_class` | `4` | Minimum character classes |
| `users_password_encrypt_method` | `YESCRYPT` | `/etc/login.defs ENCRYPT_METHOD` (POL-003 — no MD5/SHA-1) |
| `users_faillock_enabled` | `true` | Wire `pam_faillock` into PAM stack |
| `users_faillock_deny` | `5` | Failed attempts before lock |
| `users_faillock_interval` | `900` | Failure-count window (seconds) |
| `users_faillock_unlock_time` | `900` | Lockout duration for users (seconds) |
| `users_faillock_even_deny_root` | `true` | Apply lockout to root too |
| `users_faillock_root_unlock_time` | `60` | Lockout duration for root (seconds) |
| `users_login_timeout` | `60` | Shell `TMOUT` (seconds) |
| `users_umask` | `027` | Default `umask` |
| `users_disable_system_accounts` | `true` | Set `nologin` shell on unused system accounts |
| `users_lock_root` | `true` | Lock root account (`passwd -l`) |

Full list in `defaults/main.yml`.

## Account lockout (pam_faillock) — risk and recovery

`pam_faillock` locks an account after `users_faillock_deny` failed
authentications within `users_faillock_interval` seconds. With
`users_faillock_even_deny_root: true`, root is subject to the same
threshold (it unlocks faster — `users_faillock_root_unlock_time`, default
60s — so a brute-force burst cannot hold administrative access locked for
the full user window).

**Lockout risk.** A misconfigured PAM stack or an aggressive threshold can
lock out *all* interactive logins. This role enables faillock via
`pam-auth-update` profiles (which survive later `pam-auth-update` runs) and
**asserts** that `pam_faillock.so` is present in the generated stack, so a
silent mis-wire fails the play rather than producing an unenforced or
broken stack. The role is **not runtime-tested in CI** (no container); the
`users` Molecule scenario (`roles/users/molecule/default/`) asserts the
faillock lines land in `common-auth`/`common-account`.

**Recovery (break-glass).** Keep a root console / cloud serial-console
session, or a second already-authenticated session, open while applying
changes. To clear a lockout:

```bash
# Show the failure tally for a user
faillock --user <name>

# Reset it (unlock)
faillock --user <name> --reset
```

If logins are fully broken, boot to a root recovery shell (or use the
provider serial console) and either run `faillock --reset`, or move
`/usr/share/pam-configs/faillock*` aside and re-run `pam-auth-update
--package` to regenerate a clean stack. Set `users_faillock_enabled: false`
in inventory to disable lockout entirely.
