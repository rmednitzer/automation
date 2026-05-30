# ADR-002: SRE toolchain supply-chain hardening

- **Status:** Accepted
- **Date:** 2026-05-30
- **Deciders:** automation maintainers
- **Supersedes:** none (extends ADR-001 scope to `sre_toolchain`)
- **Related work:** 2026-05-30 remediation pass (findings H2, H3, M10)

## Context

`roles/sre_toolchain` installs SRE/Platform/Security binaries (kind, flux,
trivy, syft, cosign, sops, age, opa, k6, …) from upstream GitHub release
assets onto operator hosts. It was outside the 10-role validation scope of
[ADR-001](ADR-001-code-validation-baseline.md) (which covers the fleet
hardening baseline only) and so its supply-chain posture had not been
formally reviewed. The 2026-05-30 pass found three gaps between the role's
claims and its behaviour:

1. **Unverified installs were the default.** `sre_toolchain_checksum_policy`
   defaulted to `best-effort`, which installs an asset even when no SHA256
   checksum can be found — emitting only a debug warning. The role README
   and `defaults/main.yml` header simultaneously claimed the role "refuses
   unverified downloads" and is "secure-by-default". This is a
   doc-vs-behaviour contradiction with a real integrity consequence (CRA
   Annex I Part I, ISO 27001 A.8.30).
2. **No signature verification.** Signatures were never checked. The
   checksum-bundle search in `verify_checksum.yml` actively *rejected*
   `.sig` / `.asc` / `.pem` / `.cert` assets, so even projects that publish
   keyless cosign provenance gained nothing from it.
3. **Unpinned (`releases/latest`).** Every tool resolved
   `https://api.github.com/repos/<repo>/releases/latest`, so a converge
   silently consumed whatever the upstream had published most recently —
   non-reproducible, and at odds with the README's "pinned-to-latest"
   wording (which describes intent, not a pin).

The user approved a behaviour-changing redesign.

## Decision drivers

- Secure-by-default beats secure-if-configured: the safe posture must be
  what an operator gets without flags (CRA Annex I Part I).
- Reproducibility is an evidence requirement (CTL-002): the manifest must
  record exactly what was installed, by resolved tag and content hash.
- The hardening must not break the existing rescue/continue-on-failure
  tally, which lets a single tool fail without aborting the whole run.
- cosign cannot be exercised in the current CI sandbox; signature
  verification must therefore be opt-in and fully gated, validated by lint
  and syntax only here.

## Decisions

1. **`strict` is the default checksum policy.** `sre_toolchain_checksum_policy`
   now defaults to `strict`: a tool whose asset has no resolvable SHA256
   checksum is refused (the tool fails and is tallied), rather than
   installed unverified. `best-effort` remains available as an explicit,
   documented opt-out for environments that accept unverified installs.
   *(Behaviour change.)*
2. **Optional keyless cosign signature verification.** A new flag
   `sre_toolchain_verify_signatures` (default `false`) enables, per tool,
   verification of the release's signed checksum bundle
   (`<bundle>.sig` + `<bundle>.pem`) with `cosign verify-blob` against a
   configurable identity (`sre_toolchain_cosign_certificate_identity_regexp`)
   and OIDC issuer (`sre_toolchain_cosign_certificate_oidc_issuer`,
   defaulting to GitHub Actions' token service). cosign is bootstrapped from
   the catalogue *before* the install loop when verification is enabled.
   `sre_toolchain_require_signatures` (default `false`) escalates a missing
   signature from "allowed" to "abort this tool".
3. **Optional per-tool version pinning.** A tool entry in
   `roles/sre_toolchain/vars/main.yml` may carry `tag:` (or `version:`).
   When set, the role resolves `releases/tags/<tag>` instead of
   `releases/latest`. Unpinned tools continue to track latest, preserving
   current behaviour.
4. **Evidence manifest records resolved tag and SHA256.** `write_manifest.yml`
   gains an `evidence` section keyed by primary binary, recording the
   resolved `tag`, `asset`, `sha256`, whether the tool was `pinned`, and the
   `checksum` / `signature` verification outcomes. The legacy flat
   `tools: {binary: tag}` map is preserved unchanged for back-compat with
   the existing `jq '.tools[$b]'` reads on the skip path.
5. **`sre_toolchain` supply-chain posture is governed here.** This ADR
   brings `sre_toolchain` under explicit validation. ADR-001's scope
   statement remains correct (it covered the 10 hardening roles); this ADR
   is the record for the eleventh.
6. **Scratch directory is always cleaned up.** The install/manifest/report
   sequence runs inside a `block`/`always`, so
   `sre_toolchain_tmp_dir` (`/var/tmp/sre-toolchain-installer`) is removed
   even when a tool fails and the play aborts (M10).

## Consequences

- **A default `sre-toolchain.yml` run now refuses any tool without a
  published checksum.** Tools that ship no checksum (notably
  `kubectx`/`kubens`, a source tarball) are skipped under the default and
  require either `sre_toolchain_checksum_policy: best-effort` or adding the
  tool to `sre_toolchain_skip`. This is intended: unverified bytes are no
  longer installed silently.
- Operators who relied on the old permissive default must set
  `sre_toolchain_checksum_policy: best-effort` explicitly (and now own that
  decision).
- Signature verification and pinning are available but off by default, so
  no behaviour changes for existing inventories beyond the strict flip.
- cosign verification is implemented and gated but **unexecuted in CI** (no
  cosign/Docker in the sandbox); it is lint- and syntax-validated only. A
  Docker/cosign-enabled run is required before relying on it operationally.
- The evidence manifest is now reproducible-build-friendly: same pins →
  same recorded tags and hashes.

## References

- `roles/sre_toolchain/` — role implementation
- `docs/ADR-001-code-validation-baseline.md` — baseline scope (10 roles)
- CRA (EU 2024/2847) Annex I Part I — supply-chain integrity,
  secure-by-default
- ISO/IEC 27001:2022 A.8.30 — supplier-relationship security
- NIS2 (EU 2022/2555) Art 21.2(a)(e) — risk management, vulnerability
  handling
- cosign `verify-blob(1)`; Sigstore keyless signing (Fulcio / Rekor)
- POL-002 (vulnerability/patch management), CTL-002 (evidence retention)
