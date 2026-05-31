# `rsyslog_hardening` role

Hardens the **local rsyslog daemon** on Ubuntu 24.04 / 26.04 LTS. Complements
`common` (which owns journald) and `log_forwarding` / `vector` (which ship logs
to a SIEM) — this role tightens how the local daemon writes and guards logs.

## What it does

Deploys `/etc/rsyslog.d/00-hardening.conf` (named `00-` so its globals apply
before any other drop-in):

- **Restrictive create modes** — `$FileCreateMode 0640`, `$DirCreateMode 0750`,
  `$Umask 0027`, so logs rsyslog creates aren't world-readable (CIS 4.2.x).
- **Privilege drop** — `$PrivDropToUser`/`$PrivDropToGroup syslog`, so the
  daemon doesn't keep root after startup.
- **Repeated-message reduction** — collapses identical bursts (log minimisation,
  GDPR Art 5(1)(c)).

It then:

- **Validates the whole config** with `rsyslogd -N1` before any restart, so a
  bad drop-in aborts the play *before* the running daemon is touched.
- **Audits for network log reception** (`imtcp`/`imudp`). A stock host has none;
  this surfaces an unintended syslog listener. Audit-only by default — set
  `rsyslog_hardening_fail_on_network_input: true` to hard-fail instead (leave it
  false on an intended syslog server).

## Safe by design

- **Only acts when rsyslog is present** — on a journald-only host it logs a note
  and does nothing (no forced install).
- **Container-guest aware** (`rsyslog_hardening_runtime_managed`) — the drop-in
  is written, but config validation / restart are skipped in a container
  *guest*; a container/LXC **host** is managed normally.
- **Doesn't touch `log_forwarding`/`vector`** — separate drop-in; forwarding
  config is unaffected.

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `rsyslog_hardening_enabled` | `true` | Master switch |
| `rsyslog_hardening_file_create_mode` | `0640` | Mode for log files rsyslog creates |
| `rsyslog_hardening_priv_drop_user` / `_group` | `syslog` | Drop privileges to (empty user disables) |
| `rsyslog_hardening_repeated_msg_reduction` | `true` | Collapse repeated messages |
| `rsyslog_hardening_fail_on_network_input` | `false` | Hard-fail (vs. warn) if a listener is found |
| `rsyslog_hardening_manage_runtime` | `true` | Validate/restart (auto-off in container guests) |

Full list in `defaults/main.yml`.

## Compliance

CTL-003 (logging — minimisation, integrity, forensic correlation). NIS2 Art
21.2(a), GDPR Art 5(1)(c) / Art 5(1)(f), ISO 27001:2022 A.8.15.
