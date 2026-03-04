from __future__ import annotations

from pathlib import Path


def _is_path_inside(root_dir: Path, candidate: Path) -> bool:
    try:
        root_real = root_dir.resolve(strict=True)
        candidate_real = candidate.resolve(strict=True)
    except OSError:
        return False
    return root_real == candidate_real or root_real in candidate_real.parents


def _load_plugin_manifest_registry(workspace_dir: str, config: dict | None = None):
    _ = workspace_dir, config
    return {"plugins": []}


def _resolve_effective_enable_state(record: dict, root_config: dict | None):
    _ = root_config
    return {"enabled": record.get("enabled", True) is not False}


def _resolve_memory_slot_decision(record: dict, selected_id: str | None):
    kind = record.get("kind")
    if kind != "memory":
        return {"enabled": True, "selected": False}
    if selected_id and selected_id != record.get("id"):
        return {"enabled": False, "selected": False}
    return {"enabled": True, "selected": True}


def resolve_plugin_skill_dirs(workspace_dir: str | None, config: dict | None = None) -> list[str]:
    workspace = (workspace_dir or "").strip()
    if not workspace:
        return []

    registry = _load_plugin_manifest_registry(workspace, config)
    plugins = registry.get("plugins", [])
    if not plugins:
        return []

    acp_enabled = (config or {}).get("acp", {}).get("enabled", True) is not False
    selected_memory_plugin_id: str | None = None
    seen: set[str] = set()
    resolved: list[str] = []

    for record in plugins:
        skills = record.get("skills", [])
        if not skills:
            continue

        if not _resolve_effective_enable_state(record, config).get("enabled", False):
            continue
        if not acp_enabled and record.get("id") == "acpx":
            continue

        memory_decision = _resolve_memory_slot_decision(record, selected_memory_plugin_id)
        if not memory_decision.get("enabled", False):
            continue
        if memory_decision.get("selected") and record.get("kind") == "memory":
            selected_memory_plugin_id = record.get("id")

        root_dir = Path(record.get("rootDir", ""))
        for raw in skills:
            trimmed = str(raw).strip()
            if not trimmed:
                continue
            candidate = (root_dir / trimmed).resolve()
            if not candidate.exists():
                continue
            if not _is_path_inside(root_dir, candidate):
                continue
            candidate_str = str(candidate)
            if candidate_str in seen:
                continue
            seen.add(candidate_str)
            resolved.append(candidate_str)

    return resolved
