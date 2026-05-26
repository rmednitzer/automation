## Description

<!-- What does this PR change, and why? -->

## Type of change

- [ ] New role or playbook
- [ ] Role improvement or refactor
- [ ] Bug fix
- [ ] Documentation update
- [ ] Compliance change (`docs/compliance-controls.yml` or CTL-/POL-
      mapping)
- [ ] CI / tooling change

## Checklist

- [ ] Follows the [naming conventions](/rmednitzer/automation/blob/main/CLAUDE.md)
- [ ] All module references use FQCNs
- [ ] All tasks are named descriptively
- [ ] `yamllint .` passes
- [ ] `ansible-lint` passes (production profile)
- [ ] `ansible-playbook --syntax-check` passes on affected playbooks
- [ ] `make check` passes locally
- [ ] If I changed a variable in `roles/<name>/defaults/main.yml`, the
      same change is reflected in `roles/<name>/README.md` (per
      [ADR-001](/rmednitzer/automation/blob/main/docs/ADR-001-code-validation-baseline.md))
- [ ] If I added or renumbered a `CTL-*` or `POL-*` identifier,
      `docs/compliance-controls.yml`, the relevant role headers, and
      the README mapping table are all updated together
- [ ] `[Unreleased]` entry added to [`CHANGELOG.md`](/rmednitzer/automation/blob/main/CHANGELOG.md),
      citing any CTL-/POL- IDs touched
- [ ] No unencrypted secrets included in this PR

## Testing

<!-- How did you test the change? -->

## Additional notes

<!-- Anything else worth knowing -->
