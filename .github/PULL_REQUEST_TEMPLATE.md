## Description

<!-- Describe the changes in this PR -->

## Type of Change

- [ ] Bug fix
- [ ] New role or feature
- [ ] Role improvement or refactor
- [ ] Documentation update
- [ ] CI/CD change

## Checklist

- [ ] I have followed the [naming conventions](CLAUDE.md) for this project
- [ ] I have used fully qualified collection names (FQCNs) for all modules
- [ ] I have named all tasks descriptively
- [ ] I have run `yamllint .` with no errors
- [ ] I have run `ansible-lint` with no errors
- [ ] I have run `ansible-playbook --syntax-check` on affected playbooks
- [ ] I have updated relevant documentation (role READMEs, etc.)
- [ ] If I changed a variable in `roles/<name>/defaults/main.yml`, the same change is reflected in `roles/<name>/README.md` (per [ADR-001](../docs/ADR-001-code-validation-baseline.md))
- [ ] If I added or renumbered a `CTL-*` or `POL-*` identifier, `docs/compliance-controls.yml`, the relevant role headers, and the README mapping table are all updated together
- [ ] No unencrypted secrets are included in this PR

## Testing

<!-- Describe how you tested your changes -->

## Additional Notes

<!-- Any other context about this PR -->
