from __future__ import annotations

import os
from pathlib import Path


def _looks_like_skills_dir(directory: Path) -> bool:
    try:
        for entry in directory.iterdir():
            if entry.name.startswith("."):
                continue
            if entry.is_file() and entry.suffix.lower() == ".md":
                return True
            if entry.is_dir() and (entry / "SKILL.md").exists():
                return True
    except OSError:
        return False
    return False


def resolve_bundled_skills_dir(
    argv1: str | None = None,
    module_path: str | None = None,
    cwd: str | None = None,
    exec_path: str | None = None,
) -> str | None:
    override = os.getenv("OPENCLAW_BUNDLED_SKILLS_DIR", "").strip()
    if override:
        return override

    try:
        exec_file = Path(exec_path or os.sys.executable)
        sibling = exec_file.parent / "skills"
        if sibling.exists():
            return str(sibling)
    except OSError:
        pass

    search_roots: list[Path] = []
    if module_path:
        search_roots.append(Path(module_path).resolve())
    if argv1:
        search_roots.append(Path(argv1).resolve().parent)
    if cwd:
        search_roots.append(Path(cwd).resolve())

    for root in search_roots:
        current = root
        for _ in range(6):
            candidate = current / "skills"
            if _looks_like_skills_dir(candidate):
                return str(candidate)
            if current.parent == current:
                break
            current = current.parent

    return None
