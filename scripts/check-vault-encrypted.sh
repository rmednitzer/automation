#!/usr/bin/env bash
# check-vault-encrypted.sh — fail if any passed `vault.yml` file is not
# ansible-vault encrypted.
#
# The project convention (CLAUDE.md "Secrets management", H5) names every
# encrypted secrets file `vault.yml`. An ansible-vault payload always begins
# with the line `$ANSIBLE_VAULT;<version>;<cipher>`. This guard, wired into
# .pre-commit-config.yaml, refuses to let a plaintext `vault.yml` be
# committed. Plaintext `.example` templates are not named `vault.yml` and so
# are never passed to this hook.
set -euo pipefail

rc=0
for f in "$@"; do
  # Skip example/placeholder templates defensively.
  case "$f" in
    *.example | *.example.yml) continue ;;
  esac
  if [ ! -f "$f" ]; then
    continue
  fi
  first_line="$(head -n 1 "$f" 2>/dev/null || true)"
  # SC2016: the single quotes are intentional — match the literal
  # "$ANSIBLE_VAULT" header text, do not expand a shell variable.
  # shellcheck disable=SC2016
  case "$first_line" in
    '$ANSIBLE_VAULT'*) : ;;  # encrypted — OK
    *)
      echo "ERROR: $f is named vault.yml but is NOT ansible-vault encrypted." >&2
      echo "       Encrypt it with: ansible-vault encrypt $f" >&2
      rc=1
      ;;
  esac
done
exit "$rc"
