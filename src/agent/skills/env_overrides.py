from __future__ import annotations

import os
import re
from dataclasses import dataclass

from .config import resolve_skill_config
from .frontmatter import resolve_skill_key
from .types import OpenClawConfig, SkillEntry, SkillSnapshot


ALWAYS_BLOCKED_PATTERNS = [re.compile(r"^OPENSSL_CONF$", re.IGNORECASE)]


@dataclass(slots=True)
class EnvUpdate:
    key: str
    prev: str | None


def _is_dangerous_host_env_var_name(key: str) -> bool:
    blocked = {
        "PATH",
        "PYTHONPATH",
        "LD_PRELOAD",
        "DYLD_INSERT_LIBRARIES",
        "NODE_OPTIONS",
    }
    return key.upper() in blocked


def _validate_env_var_value(value: str) -> str | None:
    if "\x00" in value:
        return "Contains null bytes"
    return None


def _is_always_blocked(key: str) -> bool:
    return _is_dangerous_host_env_var_name(key) or any(p.search(key) for p in ALWAYS_BLOCKED_PATTERNS)


def _sanitize_overrides(overrides: dict[str, str], allowed_sensitive_keys: set[str]):
    allowed: dict[str, str] = {}
    blocked: list[str] = []

    for key, value in overrides.items():
        key = key.strip()
        if not key or not value:
            continue
        if _is_always_blocked(key):
            blocked.append(key)
            continue
        if key in os.environ and key not in allowed_sensitive_keys:
            continue
        warning = _validate_env_var_value(value)
        if warning == "Contains null bytes":
            blocked.append(key)
            continue
        allowed[key] = value

    return allowed, blocked


def _apply_skill_config_env_overrides(
    updates: list[EnvUpdate],
    skill_config: dict,
    primary_env: str | None,
    required_env: list[str] | None,
):
    allowed_sensitive = {e.strip() for e in (required_env or []) if e and e.strip()}
    if primary_env and primary_env.strip():
        allowed_sensitive.add(primary_env.strip())

    pending: dict[str, str] = {}
    raw_env = skill_config.get("env")
    if isinstance(raw_env, dict):
        for raw_key, env_value in raw_env.items():
            key = str(raw_key).strip()
            value = str(env_value)
            if key and value and key not in os.environ:
                pending[key] = value

    api_key = str(skill_config.get("apiKey") or "").strip()
    if primary_env and api_key and primary_env not in os.environ and primary_env not in pending:
        pending[primary_env] = api_key

    allowed, _ = _sanitize_overrides(pending, allowed_sensitive)
    for key, value in allowed.items():
        if key in os.environ:
            continue
        updates.append(EnvUpdate(key=key, prev=os.environ.get(key)))
        os.environ[key] = value


def _create_env_reverter(updates: list[EnvUpdate]):
    def revert() -> None:
        for update in updates:
            if update.prev is None:
                os.environ.pop(update.key, None)
            else:
                os.environ[update.key] = update.prev

    return revert


def apply_skill_env_overrides(skills: list[SkillEntry], config: OpenClawConfig | None = None):
    updates: list[EnvUpdate] = []
    for entry in skills:
        skill_key = resolve_skill_key(entry.skill, entry)
        skill_config = resolve_skill_config(config, skill_key)
        if not skill_config:
            continue
        primary_env = entry.metadata.primary_env if entry.metadata else None
        required_env = entry.metadata.requires.env if entry.metadata and entry.metadata.requires else None
        _apply_skill_config_env_overrides(updates, skill_config, primary_env, required_env)
    return _create_env_reverter(updates)


def apply_skill_env_overrides_from_snapshot(
    snapshot: SkillSnapshot | None = None,
    config: OpenClawConfig | None = None,
):
    if snapshot is None:
        return lambda: None

    updates: list[EnvUpdate] = []
    for skill in snapshot.skills:
        skill_config = resolve_skill_config(config, skill.name)
        if not skill_config:
            continue
        _apply_skill_config_env_overrides(
            updates,
            skill_config,
            skill.primary_env,
            skill.required_env,
        )
    return _create_env_reverter(updates)
