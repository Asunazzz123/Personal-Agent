from __future__ import annotations

import os
from pathlib import Path

from .frontmatter import resolve_skill_key
from .types import OpenClawConfig, SkillEligibilityContext, SkillEntry


DEFAULT_CONFIG_VALUES = {
    "browser.enabled": True,
    "browser.evaluateEnabled": True,
}

BUNDLED_SOURCES = {"openclaw-bundled"}


def has_binary(bin_name: str) -> bool:
    for p in os.getenv("PATH", "").split(os.pathsep):
        candidate = Path(p) / bin_name
        if candidate.exists():
            return True
        if os.name == "nt" and (Path(p) / f"{bin_name}.exe").exists():
            return True
    return False


def resolve_config_path(config: OpenClawConfig | None, path_str: str):
    current = config or {}
    for key in path_str.split("."):
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def is_config_path_truthy(config: OpenClawConfig | None, path_str: str) -> bool:
    value = resolve_config_path(config, path_str)
    if value is None and path_str in DEFAULT_CONFIG_VALUES:
        return DEFAULT_CONFIG_VALUES[path_str]
    return bool(value)


def resolve_skill_config(config: OpenClawConfig | None, skill_key: str) -> dict | None:
    skills = (config or {}).get("skills", {}).get("entries")
    if not isinstance(skills, dict):
        return None
    entry = skills.get(skill_key)
    return entry if isinstance(entry, dict) else None


def resolve_runtime_platform() -> str:
    return os.sys.platform


def _normalize_allowlist(value) -> list[str] | None:
    if not isinstance(value, list):
        return None
    normalized = [str(v).strip() for v in value if str(v).strip()]
    return normalized or None


def resolve_bundled_allowlist(config: OpenClawConfig | None = None) -> list[str] | None:
    return _normalize_allowlist((config or {}).get("skills", {}).get("allowBundled"))


def _is_bundled_skill(entry: SkillEntry) -> bool:
    return entry.skill.source in BUNDLED_SOURCES


def is_bundled_skill_allowed(entry: SkillEntry, allowlist: list[str] | None = None) -> bool:
    if not allowlist:
        return True
    if not _is_bundled_skill(entry):
        return True
    key = resolve_skill_key(entry.skill, entry)
    return key in allowlist or entry.skill.name in allowlist


def should_include_skill(
    entry: SkillEntry,
    config: OpenClawConfig | None = None,
    eligibility: SkillEligibilityContext | None = None,
) -> bool:
    skill_key = resolve_skill_key(entry.skill, entry)
    skill_config = resolve_skill_config(config, skill_key)
    if isinstance(skill_config, dict) and skill_config.get("enabled") is False:
        return False
    allow_bundled = _normalize_allowlist((config or {}).get("skills", {}).get("allowBundled"))
    if not is_bundled_skill_allowed(entry, allow_bundled):
        return False

    metadata = entry.metadata
    if metadata and metadata.os:
        platform = resolve_runtime_platform()
        remote_platforms = eligibility.remote.platforms if eligibility and eligibility.remote else []
        if platform not in metadata.os and not any(p in metadata.os for p in remote_platforms):
            return bool(metadata.always)

    if metadata and metadata.requires:
        req = metadata.requires
        if req.bins and not all(has_binary(b) for b in req.bins):
            return False
        if req.any_bins and not any(has_binary(b) for b in req.any_bins):
            return False
        if req.env:
            for env_name in req.env:
                if not os.getenv(env_name):
                    return False
        if req.config:
            for config_path in req.config:
                if not is_config_path_truthy(config, config_path):
                    return False

    return True
