## Description

<!-- Describe the changes in this PR -->

## Type of Change

- [ ] New role or playbook
- [ ] Role improvement or refactor
- [ ] Documentation update
- [ ] Compliance change (`docs/compliance-controls.yml` or CTL- / POL-
      mapping)
- [ ] CI / tooling change

## Checklist

- [ ] I have followed the [naming conventions](../CLAUDE.md) for this
      project
- [ ] All module references use fully qualified collection names (FQCNs)
- [ ] All tasks are named descriptively
- [ ] `yamllint .` passes
- [ ] `ansible-lint` passes (production profile)
- [ ] `ansible-playbook --syntax-check` passes on affected playbooks
- [ ] `make check` passes locally
- [ ] If I changed a variable in `roles/<name>/defaults/main.yml`, the
      same change is reflected in `roles/<name>/README.md` (per
      [ADR-001](../docs/ADR-001-code-validation-baseline.md))
- [ ] If I added or renumbered a `CTL-*` or `POL-*` identifier,
      `docs/compliance-controls.yml`, the relevant role headers, and the
      README mapping table are all updated together
- [ ] `[Unreleased]` entry added to [`CHANGELOG.md`](../CHANGELOG.md),
      citing any CTL- / POL- IDs touched
- [ ] No unencrypted secrets are included in this PR

## Testing

<!-- Describe how you tested your changes -->

## Additional Notes

<!-- Any other context about this PR -->
