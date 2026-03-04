from __future__ import annotations

from pathlib import Path
from typing import Callable

from .plugin_skills import resolve_plugin_skill_dirs


DEFAULT_SKILLS_WATCH_IGNORED = [
    r"(^|[\\/])\.git([\\/]|$)",
    r"(^|[\\/])node_modules([\\/]|$)",
    r"(^|[\\/])dist([\\/]|$)",
    r"(^|[\\/])\.venv([\\/]|$)",
    r"(^|[\\/])venv([\\/]|$)",
    r"(^|[\\/])__pycache__([\\/]|$)",
    r"(^|[\\/])\.mypy_cache([\\/]|$)",
    r"(^|[\\/])\.pytest_cache([\\/]|$)",
    r"(^|[\\/])build([\\/]|$)",
    r"(^|[\\/])\.cache([\\/]|$)",
]

_listeners: set[Callable[[dict], None]] = set()
_workspace_versions: dict[str, int] = {}
_watchers: dict[str, dict] = {}
_global_version = 0


class _NoopWatcher:
    def close(self):
        return None


def _bump_version(current: int) -> int:
    now = int(__import__("time").time() * 1000)
    return current + 1 if now <= current else now


def _emit(event: dict) -> None:
    for listener in list(_listeners):
        try:
            listener(event)
        except Exception:
            pass


def _resolve_watch_paths(workspace_dir: str, config: dict | None = None) -> list[str]:
    paths: list[str] = []
    workspace = workspace_dir.strip()
    if workspace:
        paths.append(str(Path(workspace) / "skills"))
        paths.append(str(Path(workspace) / ".agents" / "skills"))

    home = str(Path.home())
    paths.append(str(Path(home) / ".codex" / "skills"))
    paths.append(str(Path(home) / ".agents" / "skills"))

    extra = (config or {}).get("skills", {}).get("load", {}).get("extraDirs", [])
    for item in extra:
        value = str(item).strip()
        if value:
            paths.append(str(Path(value).expanduser().resolve()))

    paths.extend(resolve_plugin_skill_dirs(workspace, config))
    return paths


def _to_watch_glob_root(raw: str) -> str:
    return raw.replace("\\", "/").rstrip("/")


def resolve_watch_targets(workspace_dir: str, config: dict | None = None) -> list[str]:
    targets: set[str] = set()
    for root in _resolve_watch_paths(workspace_dir, config):
        glob_root = _to_watch_glob_root(root)
        targets.add(f"{glob_root}/SKILL.md")
        targets.add(f"{glob_root}/*/SKILL.md")
    return sorted(targets)


def register_skills_change_listener(listener: Callable[[dict], None]):
    _listeners.add(listener)

    def unregister() -> None:
        _listeners.discard(listener)

    return unregister


def bump_skills_snapshot_version(
    workspace_dir: str | None = None,
    reason: str = "manual",
    changed_path: str | None = None,
) -> int:
    global _global_version
    if workspace_dir:
        current = _workspace_versions.get(workspace_dir, 0)
        next_value = _bump_version(current)
        _workspace_versions[workspace_dir] = next_value
        _emit({"workspaceDir": workspace_dir, "reason": reason, "changedPath": changed_path})
        return next_value

    _global_version = _bump_version(_global_version)
    _emit({"reason": reason, "changedPath": changed_path})
    return _global_version


def get_skills_snapshot_version(workspace_dir: str | None = None) -> int:
    if not workspace_dir:
        return _global_version
    return max(_global_version, _workspace_versions.get(workspace_dir, 0))


def ensure_skills_watcher(workspace_dir: str, config: dict | None = None, watch_factory=None) -> None:
    workspace = workspace_dir.strip()
    if not workspace:
        return

    watch_enabled = (config or {}).get("skills", {}).get("load", {}).get("watch", True) is not False
    debounce_raw = (config or {}).get("skills", {}).get("load", {}).get("watchDebounceMs")
    debounce_ms = max(0, int(debounce_raw)) if isinstance(debounce_raw, (int, float)) else 250

    existing = _watchers.get(workspace)
    if not watch_enabled:
        if existing:
            try:
                existing["watcher"].close()
            finally:
                _watchers.pop(workspace, None)
        return

    targets = resolve_watch_targets(workspace, config)
    path_key = "|".join(targets)
    if existing and existing.get("pathsKey") == path_key and existing.get("debounceMs") == debounce_ms:
        return

    if existing:
        try:
            existing["watcher"].close()
        finally:
            _watchers.pop(workspace, None)

    watcher = watch_factory(targets, debounce_ms) if watch_factory else _NoopWatcher()
    _watchers[workspace] = {
        "watcher": watcher,
        "pathsKey": path_key,
        "debounceMs": debounce_ms,
    }
