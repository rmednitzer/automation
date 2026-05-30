# `sre_toolchain` role

SRE/Platform/Security toolchain installer from upstream GitHub releases.
By default it **refuses any download without a verifiable SHA256 checksum**
(`sre_toolchain_checksum_policy: strict`), optionally verifies keyless
cosign signatures, optionally pins tools to specific release tags, and
records resolved tags + content hashes in a JSON evidence manifest. Targets
operator hosts (workstation, admin/bastion, CI runner) — **not** part of
the fleet baseline applied by the hardening roles.

Supply-chain posture is governed by
[ADR-002](../../docs/ADR-002-sre-toolchain-supply-chain.md).

## What it installs

Tools resolved against the GitHub release API of each upstream repository —
`releases/tags/<tag>` when the catalogue entry pins a `tag:`/`version:`,
otherwise `releases/latest`:

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
- Downloads the asset and computes its SHA256 (recorded as evidence)
- Verifies the SHA256 against the per-asset `*.sha256` / `*.sha256sum`
  file when published, else searches the release's bundle checksum files
  (`SHA256SUMS`, `checksums.txt`, etc.)
- Honours `sre_toolchain_checksum_policy`: **`strict` (default)** aborts a
  tool when no checksum is found; `best-effort` logs and proceeds with an
  unverified install (opt-in)
- Optionally (`sre_toolchain_verify_signatures: true`) verifies the signed
  checksum bundle (`<bundle>.sig` + `<bundle>.pem`) with `cosign
  verify-blob` against the configured identity/issuer, bootstrapping
  `cosign` first; `sre_toolchain_require_signatures` makes a missing
  signature fatal
- Optionally pins a tool to a release tag via `tag:`/`version:` in
  `vars/main.yml` (resolves `releases/tags/<tag>`)
- Installs binaries into `sre_toolchain_dest_dir` (`0755`, `root:root`)
- Records installed versions in a JSON manifest (default
  `{{ sre_toolchain_dest_dir }}/.sre-toolchain-versions.json`) — both a
  flat `tools: {binary: tag}` map and an `evidence` section with the
  resolved tag, asset, SHA256, pin flag, and checksum/signature outcomes
  for CTL-002 evidence retention
- Removes the scratch download directory after every run
- Skips tools whose binaries already exist unless
  `sre_toolchain_force` is set
- `kubectx`/`kubens` ship as a source tarball with **no upstream
  checksum**, so under the default `strict` policy they are skipped; set
  `sre_toolchain_checksum_policy: best-effort` (or add `kubectx` to
  `sre_toolchain_skip`) to opt in

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `sre_toolchain_dest_dir` | `/usr/local/bin` | Install target directory |
| `sre_toolchain_force` | `false` | Overwrite binaries already present |
| `sre_toolchain_checksum_policy` | `strict` | **Default `strict`**: abort a tool with no published checksum. `best-effort` proceeds with an unverified install (opt-in). |
| `sre_toolchain_verify_signatures` | `false` | Verify the signed checksum bundle with `cosign verify-blob` |
| `sre_toolchain_require_signatures` | `false` | When verifying, treat a missing signature as fatal |
| `sre_toolchain_cosign_certificate_oidc_issuer` | GitHub Actions token URL | `--certificate-oidc-issuer` for cosign |
| `sre_toolchain_cosign_certificate_identity_regexp` | GitHub workflow regex | `--certificate-identity-regexp` for cosign (tighten per tool) |
| `sre_toolchain_version_log` | `{{ sre_toolchain_dest_dir }}/.sre-toolchain-versions.json` | JSON manifest of installed versions + evidence |
| `sre_toolchain_github_token` | `""` | GitHub API token; recommended to avoid 60/hr rate limits |
| `sre_toolchain_tmp_dir` | `/var/tmp/sre-toolchain-installer` | Scratch directory for downloads (mode `0700`, removed after each run) |
| `sre_toolchain_skip` | `[]` | Tool names (or the first binary of a multi-bin entry) to skip |

The full tool catalogue and asset patterns live in `vars/main.yml` and
are not intended to be overridden per-host — change the role rather
than inventory. To **pin** a tool, add `tag:` (or `version:`) to its
catalogue entry there; the resolved tag and SHA256 are then recorded in the
evidence manifest.

## Compliance

| Reference | Mapping |
|-----------|---------|
| NIS2 Art 21.2(a) | Risk-analysis and information-system security policies (verified supply of operator tooling) |
| NIS2 Art 21.2(e) | Vulnerability handling — checksum verification, supply-chain integrity |
| CRA Annex I Part I | Secure-by-default — refuses unverified downloads by default (`strict`); optional cosign signature verification |
| ISO 27001:2022 A.8.30 | Supplier-relationship security — checksum proof, optional signature provenance, optional tag pinning |
| POL-002 | Vulnerability and patch management — re-running the role pulls latest (or pinned) releases |
| CTL-002 | Evidence retention — manifest persists resolved tags, SHA256s, and verification outcomes |

## Usage

```bash
# Standalone playbook (recommended)
ansible-playbook -i inventories/<env>/hosts playbooks/sre-toolchain.yml

# With a GitHub token via environment (kept out of git)
ansible-playbook -i inventories/<env>/hosts playbooks/sre-toolchain.yml \
  -e sre_toolchain_github_token="$GITHUB_TOKEN"

# Strict checksum enforcement is the DEFAULT (fails any tool without a
# published checksum). Opt out to the legacy permissive behaviour with:
ansible-playbook -i inventories/<env>/hosts playbooks/sre-toolchain.yml \
  -e sre_toolchain_checksum_policy=best-effort

# Verify keyless cosign signatures (bootstraps cosign first)
ansible-playbook -i inventories/<env>/hosts playbooks/sre-toolchain.yml \
  -e sre_toolchain_verify_signatures=true

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
