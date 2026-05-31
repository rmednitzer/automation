# `ollama` role

Provisions a **local LLM inference runtime** ([Ollama](https://ollama.com)) on a
dedicated inference host (e.g. the GPU compute host) — Ubuntu 24.04 / 26.04 LTS.
The first of the AI-native capabilities; keeps inference **on-premises** so
prompts and data never leave the estate for a third-party model API.

> Targets **inference hosts**, not the fleet baseline — run via
> [`playbooks/local-inference.yml`](../../playbooks/local-inference.yml), not
> `site-common.yml`. **Off by default.**

## What it does

- Installs a **pinned, checksum-verified** Ollama release (GitHub release tgz →
  `get_url` with `checksum:` → extract to `{{ ollama_install_prefix }}`), the
  ADR-002 supply-chain pattern. No `curl | sh`.
- Creates the `ollama` system user and data dir, and a **hardened systemd unit**
  (`NoNewPrivileges`, `ProtectSystem=full`, `ProtectHome`, `PrivateTmp`, …;
  moderate because GPU access needs device nodes).
- Binds **localhost only** by default (the Ollama API is unauthenticated).
- Optionally pulls a configured list of models.

## Security model (POL-004)

- **Off by default**; requires a pinned `ollama_version` + `ollama_checksum`
  (asserted) — no floating "latest".
- **Localhost-bound** (`ollama_host: 127.0.0.1`). The API has **no auth**, so do
  not expose it on the network without a fronting authenticated proxy.
- **Data sovereignty** — inference runs locally; Confidential/Restricted data
  isn't sent to a hosted AI API (GDPR Art 25 / Art 44).
- Hardened service account (system user, `nologin`) and systemd sandboxing.

## Prerequisites

- An NVIDIA driver on the host for GPU acceleration (the role checks `nvidia-smi`
  and warns, falling back to CPU; it does **not** install drivers).
- The `ollama_version`'s published SHA256, pinned out-of-band.

## Usage

```yaml
# inventories/<env>/group_vars/inference_hosts.yml
ollama_enabled: true
ollama_version: "0.5.7"
ollama_checksum: "sha256:<published-hex>"
ollama_models:
  - "llama3.1:8b"
# ollama_host: "127.0.0.1"   # keep localhost unless fronted by an auth proxy
```

```bash
ansible-playbook -i inventories/<env>/hosts playbooks/local-inference.yml
```

## Key variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ollama_enabled` | `false` | Master switch (the playbook sets it true) |
| `ollama_version` | `""` | **Required** — pinned release, e.g. `0.5.7` |
| `ollama_checksum` | `""` | **Required** — `sha256:<hex>` or a checksum URL |
| `ollama_host` / `ollama_port` | `127.0.0.1` / `11434` | Bind address (keep localhost) |
| `ollama_models` | `[]` | Models to pull, e.g. `["llama3.1:8b"]` |
| `ollama_gpu_groups` | `[video, render]` | Groups for NVIDIA device access |
| `ollama_manage_runtime` | `true` | Manage service/pulls (auto-off in container guests) |

Full list in `defaults/main.yml`.

## Compliance

POL-004 (data classification & handling — local inference keeps data
on-premises). GDPR Art 25 / Art 5(1)(f) / Art 44, NIS2 Art 21.2(e), ISO
27001:2022 A.5.12 / A.8.9.

## Engine choice

Ollama is the default for single-GPU local serving (simple, systemd-friendly,
built-in model management, OpenAI-compatible `/v1` API). A higher-throughput
serving engine (e.g. vLLM) would be a **sibling role**, not a flag here.
