---
name: real-skill-python-maintainer
description: Maintain and extend the Python skills runtime project. Use when tasks involve adding or modifying modules under skill_python, updating skill parsing/filtering/watch logic, refining workspace skill loading behavior, or keeping tests in sync with runtime behavior.
---

# Purpose

Implement, test, and document changes to the Python port of the skills runtime.

# Workflow

1. Read affected modules under `skill_python/` and map call flow before editing.
2. Keep behavior aligned with existing tests unless the task explicitly changes behavior.
3. Prefer small deterministic functions and avoid hidden global side effects.
4. Preserve backward-compatible function signatures unless migration is requested.
5. Add or update `pytest` tests under `tests/` for every behavior change.
6. Run `python -m pytest -q` and fix regressions before finishing.

# Editing Rules

- Keep frontmatter keys stable for parsers that expect string values.
- Validate user-facing defaults and edge cases (empty lists, missing metadata, invalid install specs).
- Keep path handling cross-platform using `pathlib`.
- For environment overrides, block dangerous keys and make rollback explicit.

# Output Checklist

1. Explain what changed and why.
2. List modified files.
3. Report exact test command and result.
4. Note any behavior differences from previous implementation.