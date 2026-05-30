# `ssh_hardening` role

SSH server hardening for Ubuntu 24.04 LTS.

## What it does

- Deploys a hardened `/etc/ssh/sshd_config` with `sshd -t -f %s`
  validation before apply and a backup of the prior file
- Disables password authentication and keyboard-interactive (key-only —
  POL-001)
- Restricts root login per `ssh_permit_root_login`
- Prunes weak Diffie–Hellman moduli (< 3071 bits) from
  `/etc/ssh/moduli`
- Selects BSI TR-02102-4 / Mozilla-modern aligned KEX, ciphers, MACs,
  and host-key algorithms (POL-003 — no SHA-1, no CBC, Ed25519
  preferred)
- Configures session timeouts, max auth attempts, and `MaxStartups`
  connection throttling (CIS §5); binds to `ssh_listen_addresses`
  (all interfaces by default); disables agent / X11 / TCP forwarding by
  default
- Deploys a legal monitoring banner (GDPR Art 5(2), NIS2 Art 21.2(a))
- Optionally restricts access to specific users / groups
  (`AllowUsers` / `AllowGroups`)

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ssh_port` | `22` | SSH listen port (see cross-role coupling note in `group_vars/all.yml`) |
| `ssh_permit_root_login` | `"no"` | `PermitRootLogin` value |
| `ssh_password_authentication` | `false` | Allow password authentication |
| `ssh_pubkey_authentication` | `true` | Allow public-key authentication |
| `ssh_permit_empty_passwords` | `false` | Allow empty passwords |
| `ssh_challenge_response_authentication` | `false` | Allow keyboard-interactive |
| `ssh_max_auth_tries` | `3` | Max auth attempts per connection |
| `ssh_max_sessions` | `3` | Max concurrent sessions per connection |
| `ssh_max_startups` | `"10:30:60"` | `MaxStartups` unauthenticated-connection throttle (CIS §5) |
| `ssh_listen_addresses` | list — `["0.0.0.0", "::"]` | `ListenAddress` entries (default all interfaces) |
| `ssh_login_grace_time` | `20` | Seconds to authenticate before disconnect |
| `ssh_client_alive_interval` | `300` | Idle keepalive interval (seconds) |
| `ssh_client_alive_count_max` | `2` | Idle keepalives before disconnect |
| `ssh_kex_algorithms` | list — `[curve25519-sha256, curve25519-sha256@libssh.org, diffie-hellman-group16-sha512, diffie-hellman-group18-sha512]` | Permitted KEX algorithms |
| `ssh_ciphers` | list — `[chacha20-poly1305@openssh.com, aes256-gcm@openssh.com, aes128-gcm@openssh.com, aes256-ctr]` | Permitted symmetric ciphers |
| `ssh_macs` | list — `[hmac-sha2-512-etm@openssh.com, hmac-sha2-256-etm@openssh.com, hmac-sha2-512, hmac-sha2-256]` | Permitted MAC algorithms |
| `ssh_host_key_algorithms` | list — `[ssh-ed25519, rsa-sha2-512, rsa-sha2-256]` | Permitted host-key algorithms |
| `ssh_allow_agent_forwarding` | `false` | Allow agent forwarding |
| `ssh_allow_tcp_forwarding` | `false` | Allow TCP port forwarding |
| `ssh_x11_forwarding` | `false` | Allow X11 forwarding |
| `ssh_banner_enabled` | `true` | Deploy legal banner |
| `ssh_banner_path` | `/etc/ssh/banner` | Banner file path |
| `ssh_allowed_users` | `[]` | If set, render `AllowUsers` |
| `ssh_allowed_groups` | `[]` | If set, render `AllowGroups` |

Full list in `defaults/main.yml`.
