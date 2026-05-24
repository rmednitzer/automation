# Users Role

User management, sudo hardening, password policy, and account lockout
for Ubuntu 24.04 LTS.

## What it does

- Configures password aging and complexity via PAM (`pam_pwquality`)
  and `/etc/login.defs`
- Wires `pam_faillock` into `common-auth` and `common-account` and
  templates `/etc/security/faillock.conf` so the lockout policy is
  actually enforced
- Sets the stored-password hash to `YESCRYPT` (POL-003)
- Hardens sudo with full I/O logging, lecture, restricted `secure_path`,
  and `visudo -cf` validation on the deployed dropin
- Creates managed user accounts and deploys SSH keys via
  `ansible.posix.authorized_key`
- Sets restrictive home directory permissions (`0750`)
- Configures system-wide `umask` and shell login `TMOUT`
- Sets `nologin` on unused system accounts
- Locks the root account by default (administrative access via sudo)

## Key Variables

| Variable                              | Default     | Description |
|---------------------------------------|-------------|-------------|
| `users_managed`                       | `[]`        | List of user accounts to manage (`name`, `groups`, `shell`, `ssh_keys`, `state`) |
| `users_sudo_group`                    | `sudo`      | Group granted sudo |
| `users_sudo_passwordless`             | `false`     | Allow passwordless sudo for `users_sudo_group` |
| `users_sudo_require_tty`              | `false`     | `Defaults requiretty` in sudoers (kept off so Ansible's no-TTY `become` keeps working — see defaults comment) |
| `users_password_max_days`             | `90`        | Password expiry (days) |
| `users_password_min_days`             | `7`         | Minimum days between password changes |
| `users_password_warn_days`            | `14`        | Warn before expiry (days) |
| `users_password_min_length`           | `14`        | Minimum password length (`pwquality` `minlen`) |
| `users_password_remember`             | `12`        | Password-history depth (`pam_unix remember=`) |
| `users_password_min_class`            | `4`         | Minimum character classes |
| `users_password_encrypt_method`       | `YESCRYPT`  | `/etc/login.defs ENCRYPT_METHOD` (POL-003 — no MD5/SHA-1) |
| `users_faillock_enabled`              | `true`      | Wire `pam_faillock` into PAM stack |
| `users_faillock_deny`                 | `5`         | Failed attempts before lock |
| `users_faillock_interval`             | `900`       | Failure-count window (seconds) |
| `users_faillock_unlock_time`          | `900`       | Lockout duration for users (seconds) |
| `users_faillock_even_deny_root`       | `true`      | Apply lockout to root too |
| `users_faillock_root_unlock_time`     | `60`        | Lockout duration for root (seconds) |
| `users_login_timeout`                 | `60`        | Shell `TMOUT` (seconds) |
| `users_umask`                         | `027`       | Default `umask` |
| `users_disable_system_accounts`       | `true`      | Set `nologin` shell on unused system accounts |
| `users_lock_root`                     | `true`      | Lock root account (`passwd -l`) |

See `defaults/main.yml` for the full list.
