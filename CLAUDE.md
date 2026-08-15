# Working in this repository

This project is **NA**.

## Orient yourself — run this first

```bash
argos context              # artefact counts, next IDs, conventions, active diagnostics
argos tree                 # requirement DAG with status and ASIL
```

## Workflow rules

- **Every task starts with PROC-00014-2 (Start Task).** Read it before writing
  any artefact:
  ```bash
  argos get PROC-00014-2
  ```
- This project is **NA** (no ASIL declared). Agents may act as Owner
  under PROTOCOL-autonomous-loop (Autonomous Development Loop). The loop
  reads this signal from ``argos.toml [project].asil``.

- New artefacts start at DRAFT. Promote to APPROVED only after Owner sign-off.
- Commits: imperative summary of what was produced or changed.

## Definition of Done

```bash
python -m pytest && pre-commit run --all-files
```

## Baseline diagnostics (not regressions)

- `W-SREQ-NOT-DECOMPOSED` on SREQ-00001-1 (the umbrella decomposes into
  the other SREQs, not into local REQs) and SREQ-00006-1 (argos
  integration — phase-2 roadmap, decomposed when its milestone starts).
