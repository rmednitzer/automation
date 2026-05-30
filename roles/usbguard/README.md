# `usbguard` role

Audits the USB attack surface and, opt-in, enforces a **default-deny USB device
allow-list** with USBGuard, on Ubuntu 24.04 / 26.04 LTS.

USBGuard blocks unauthorised USB devices — BadUSB / rogue-HID injectors, covert
mass-storage exfiltration, malicious network adapters — at the physical device
boundary, the default-deny complement to the `apparmor` MAC layer.

## What it does

- Installs `usbguard`.
- **Audits** the USB attack surface: counts currently-connected devices via
  `usbguard generate-policy` (reads sysfs; no daemon needed) — read-only.
- **Opt-in**, enables the blocking daemon: bootstraps an allow-list from the
  devices connected right now, deploys the daemon policy, and starts
  `usbguard.service`.

## Safe by default — and lock-out aware

USB blocking is **disruptive on physical hosts** (a wrong policy can detach the
console keyboard/mouse), so the role is conservative:

- **Enforcement is opt-in.** `usbguard_enforce` is `false` by default — a
  baseline run installs USBGuard and audits the device count but does **not**
  enable the blocking daemon.
- **Connected devices are never deauthorised.** When you do enforce,
  `PresentDevicePolicy=keep` leaves already-attached devices (keyboard, mouse,
  existing storage) in their authorised state, and `PresentControllerPolicy=keep`
  never blacks out the USB controllers. Only **newly inserted** devices are
  evaluated against the allow-list (`InsertedDevicePolicy=apply-policy`,
  `ImplicitPolicyTarget=block`) — that is where the protection is.
- **The allow-list is seeded from the live machine.** On first enforce the rule
  set is generated from the devices connected at that moment, so the console
  input devices are allow-listed. The rule file is then **operator-managed**
  (the role won't regenerate it).
- **Container-guest aware** (`usbguard_runtime_managed`): USB authorization is a
  host-hardware property, so container *guests* skip entirely; a container/LXC
  **host** is managed normally — same `ansible_virtualization_role == 'guest'`
  pattern as `auditd` / `kernel_lockdown`.

> First enforce on a physical host with **out-of-band/console access**, and
> review `/etc/usbguard/rules.conf` before relying on it.

## Usage

```yaml
# inventories/<env>/group_vars/<group>.yml
usbguard_enforce: true        # enable the blocking daemon (default false)
# Optional: stricter handling of already-connected devices once the rules are
# validated (default "keep" never deauthorises them):
# usbguard_present_device_policy: apply-policy
```

Manage the allow-list afterwards with the `usbguard` CLI
(`usbguard list-devices`, `usbguard allow-device <id>`,
`usbguard generate-policy`), then persist with `usbguard generate-policy`.

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `usbguard_enabled` | `true` | Master switch (install + audit only until enforce) |
| `usbguard_enforce` | `false` | Enable the blocking daemon (opt-in) |
| `usbguard_implicit_policy_target` | `block` | Unmatched device: `block` / `reject` / `allow` |
| `usbguard_present_device_policy` | `keep` | Already-connected devices on start (`keep` = don't touch) |
| `usbguard_inserted_device_policy` | `apply-policy` | Newly inserted devices (evaluate vs rules) |
| `usbguard_audit` | `true` | Report the connected-device count (read-only) |
| `usbguard_manage_runtime` | `true` | Manage install/daemon (auto-off in container guests) |

Full list in `defaults/main.yml`.

## Compliance

POL-001 (access control — default-deny USB device authorization, the physical
complement to user-level access control). CRA Annex I Part I, NIS2 Art 21.2(e),
GDPR Art 5(1)(f) / Art 25, ISO 27001:2022 A.8.3 / A.7.10.
