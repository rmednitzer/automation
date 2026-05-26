# `sre_toolchain` role

Pinned-to-latest SRE/Platform/Security toolchain installer from upstream
GitHub releases with SHA256 verification and a JSON manifest of
installed versions. Targets operator hosts (workstation, admin/bastion,
CI runner) — **not** part of the fleet baseline applied by the
hardening roles.

## What it installs

Tools resolved against the GitHub `releases/latest` endpoint of each
upstream repository:

| Category | Tools |
|----------|-------|
| Kubernetes core | `kind`, `kustomize`, `stern`, `kubectx`, `kubens` |
| GitOps | `flux` |
| Supply chain & SBOM | `trivy`, `syft`, `cosign`, `sops`, `age`, `age-keygen` |
| Policy | `opa`, `conftest` |
| Load testing | `k6` |
| Manifest lint / verify | `kubeconform`, `kube-score`, `kube-linter` |
| Container inspection | `dive` |

Architecture is detected automatically. Supported: `amd64` (`x86_64`)
and `arm64` (`aarch64`) on Linux.

## What it does

- Resolves architecture facts and validates required CLI dependencies
  (`curl`, `jq`, `tar`, `unzip`, `sha256sum`) up-front
- Fetches each release's JSON metadata via the GitHub API; honours
  `sre_toolchain_github_token` for rate-limited environments
- Selects the matching release asset by regex, with an optional
  fallback pattern (used for `k6` whose asset naming has drifted)
- Downloads the asset, verifies its SHA256 against the per-asset
  `*.sha256` / `*.sha256sum` file when published, else searches the
  release's bundle checksum files (`SHA256SUMS`, `checksums.txt`, etc.)
- Honours `sre_toolchain_checksum_policy`: `strict` aborts a tool when
  no checksum is found; `best-effort` logs and proceeds
- Installs binaries into `sre_toolchain_dest_dir` (`0755`, `root:root`)
- Records installed versions in a JSON manifest (default
  `{{ sre_toolchain_dest_dir }}/.sre-toolchain-versions.json`) for
  CTL-002 evidence retention
- Skips tools whose binaries already exist unless
  `sre_toolchain_force` is set
- `kubectx`/`kubens` ship as a source tarball with no upstream
  checksum; handled by its own task file and intentionally skipped
  under `sre_toolchain_checksum_policy: strict`

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `sre_toolchain_dest_dir` | `/usr/local/bin` | Install target directory |
| `sre_toolchain_force` | `false` | Overwrite binaries already present |
| `sre_toolchain_checksum_policy` | `best-effort` | `strict` aborts a tool with no published checksum |
| `sre_toolchain_version_log` | `{{ sre_toolchain_dest_dir }}/.sre-toolchain-versions.json` | JSON manifest of installed versions |
| `sre_toolchain_github_token` | `""` | GitHub API token; recommended to avoid 60/hr rate limits |
| `sre_toolchain_tmp_dir` | `/var/tmp/sre-toolchain-installer` | Scratch directory for downloads (mode `0700`) |
| `sre_toolchain_skip` | `[]` | Tool names (or the first binary of a multi-bin entry) to skip |

The full tool catalogue and asset patterns live in `vars/main.yml` and
are not intended to be overridden per-host — change the role rather
than inventory.

## Compliance

| Reference | Mapping |
|-----------|---------|
| NIS2 Art 21.2(a) | Risk-analysis and information-system security policies (verified supply of operator tooling) |
| NIS2 Art 21.2(e) | Vulnerability handling — checksum verification, supply-chain integrity |
| CRA Annex I Part I | Secure-by-default — refuses unverified downloads under `strict` policy |
| ISO 27001:2022 A.8.30 | Supplier-relationship security — pinned-to-upstream-release with checksum proof |
| POL-002 | Vulnerability and patch management — re-running the role pulls latest releases |
| CTL-002 | Evidence retention — manifest persists installed versions and policy |

## Usage

```bash
# Standalone playbook (recommended)
ansible-playbook -i inventories/<env>/hosts playbooks/sre-toolchain.yml

# With a GitHub token via environment (kept out of git)
ansible-playbook -i inventories/<env>/hosts playbooks/sre-toolchain.yml \
  -e sre_toolchain_github_token="$GITHUB_TOKEN"

# Strict mode — fail any tool without a published checksum
ansible-playbook -i inventories/<env>/hosts playbooks/sre-toolchain.yml \
  -e sre_toolchain_checksum_policy=strict

# Force re-install all binaries
ansible-playbook -i inventories/<env>/hosts playbooks/sre-toolchain.yml \
  -e sre_toolchain_force=true

# Skip specific tools
ansible-playbook -i inventories/<env>/hosts playbooks/sre-toolchain.yml \
  -e '{"sre_toolchain_skip":["k6","dive"]}'
```

## Notes

- Not part of `playbooks/site-common.yml` — targets operator hosts, not
  the hardened fleet baseline.
- Requires outbound HTTPS to `api.github.com` and
  `github.com` / `objects.githubusercontent.com`.
- Re-runs are idempotent: tools already present are skipped unless
  `sre_toolchain_force` is set.
