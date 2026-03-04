from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from .config import should_include_skill
from .filtering import normalize_skill_filter
from .frontmatter import parse_frontmatter, resolve_openclaw_metadata, resolve_skill_invocation_policy
from .serialize import serialize_by_key
from .types import (
    Skill,
    SkillCommandDispatchSpec,
    SkillCommandSpec,
    SkillEligibilityContext,
    SkillEntry,
    SkillSnapshot,
    SkillSnapshotSkill,
)

SKILL_COMMAND_MAX_LENGTH = 32
SKILL_COMMAND_FALLBACK = "skill"
SKILL_COMMAND_DESCRIPTION_MAX_LENGTH = 100

DEFAULT_MAX_SKILLS_IN_PROMPT = 150
DEFAULT_MAX_SKILLS_PROMPT_CHARS = 30_000
DEFAULT_MAX_SKILL_FILE_BYTES = 256_000


def format_skills_for_prompt(skills: list[Skill]) -> str:
    if not skills:
        return ""
    lines = ["Available skills:"]
    for skill in skills:
        lines.append(f"- {skill.name}: {skill.description} ({skill.file_path})")
    return "\n".join(lines)


def _compact_skill_paths(skills: list[Skill]) -> list[Skill]:
    home = str(Path.home())
    prefix = home if home.endswith(os.sep) else f"{home}{os.sep}"
    return [
        Skill(
            name=s.name,
            description=s.description,
            file_path=(f"~/{s.file_path[len(prefix):]}" if s.file_path.startswith(prefix) else s.file_path),
            base_dir=s.base_dir,
            source=s.source,
        )
        for s in skills
    ]


def _skill_from_file(skill_file: Path, source: str) -> Skill | None:
    try:
        if skill_file.stat().st_size > DEFAULT_MAX_SKILL_FILE_BYTES:
            return None
        content = skill_file.read_text(encoding="utf-8")
    except OSError:
        return None

    frontmatter = parse_frontmatter(content)
    name = frontmatter.get("name") or skill_file.parent.name
    description = frontmatter.get("description") or name
    return Skill(name=name, description=description, file_path=str(skill_file), base_dir=str(skill_file.parent), source=source)


def _load_skills_from_root(root: Path, source: str) -> list[Skill]:
    if not root.exists() or not root.is_dir():
        return []

    root_skill = root / "SKILL.md"
    if root_skill.exists():
        skill = _skill_from_file(root_skill, source)
        return [skill] if skill else []

    skills: list[Skill] = []
    for child in sorted([p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")]):
        skill_md = child / "SKILL.md"
        if skill_md.exists():
            parsed = _skill_from_file(skill_md, source)
            if parsed:
                skills.append(parsed)
    return skills


def load_workspace_skill_entries(
    workspace_dir: str,
    config: dict | None = None,
    managed_skills_dir: str | None = None,
    bundled_skills_dir: str | None = None,
) -> list[SkillEntry]:
    workspace = Path(workspace_dir).resolve()
    managed = Path(managed_skills_dir or (Path.home() / ".codex" / "skills"))
    personal_agents = Path.home() / ".agents" / "skills"
    project_agents = workspace / ".agents" / "skills"
    workspace_skills = workspace / "skills"

    roots: list[tuple[Path, str]] = []
    extra_dirs = (config or {}).get("skills", {}).get("load", {}).get("extraDirs", [])
    for item in extra_dirs:
        value = str(item).strip()
        if value:
            roots.append((Path(value).expanduser().resolve(), "openclaw-extra"))
    if bundled_skills_dir:
        roots.append((Path(bundled_skills_dir).resolve(), "openclaw-bundled"))
    roots.extend(
        [
            (managed, "openclaw-managed"),
            (personal_agents, "agents-skills-personal"),
            (project_agents, "agents-skills-project"),
            (workspace_skills, "openclaw-workspace"),
        ]
    )

    merged: dict[str, Skill] = {}
    for root, source in roots:
        for skill in _load_skills_from_root(root, source):
            merged[skill.name] = skill

    entries: list[SkillEntry] = []
    for skill in merged.values():
        try:
            raw = Path(skill.file_path).read_text(encoding="utf-8")
        except OSError:
            raw = ""
        frontmatter = parse_frontmatter(raw)
        entries.append(
            SkillEntry(
                skill=skill,
                frontmatter=frontmatter,
                metadata=resolve_openclaw_metadata(frontmatter),
                invocation=resolve_skill_invocation_policy(frontmatter),
            )
        )
    return entries


def _filter_skill_entries(
    entries: list[SkillEntry],
    config: dict | None = None,
    skill_filter: list[str] | None = None,
    eligibility: SkillEligibilityContext | None = None,
) -> list[SkillEntry]:
    filtered = [e for e in entries if should_include_skill(e, config, eligibility)]
    if skill_filter is not None:
        normalized = normalize_skill_filter(skill_filter) or []
        filtered = [e for e in filtered if e.skill.name in normalized] if normalized else []
    return filtered


def _apply_prompt_limits(skills: list[Skill], config: dict | None = None):
    limits = (config or {}).get("skills", {}).get("limits", {})
    max_count = int(limits.get("maxSkillsInPrompt", DEFAULT_MAX_SKILLS_IN_PROMPT))
    max_chars = int(limits.get("maxSkillsPromptChars", DEFAULT_MAX_SKILLS_PROMPT_CHARS))

    sliced = skills[:max(0, max_count)]
    truncated = len(skills) > len(sliced)

    while len(format_skills_for_prompt(sliced)) > max_chars and sliced:
        sliced.pop()
        truncated = True

    return sliced, truncated


def _resolve_prompt_state(
    workspace_dir: str,
    config: dict | None = None,
    entries: list[SkillEntry] | None = None,
    skill_filter: list[str] | None = None,
    eligibility: SkillEligibilityContext | None = None,
):
    skill_entries = entries or load_workspace_skill_entries(workspace_dir, config)
    eligible = _filter_skill_entries(skill_entries, config, skill_filter, eligibility)
    prompt_entries = [e for e in eligible if not (e.invocation and e.invocation.disable_model_invocation)]
    resolved_skills = [e.skill for e in prompt_entries]
    skills_for_prompt, truncated = _apply_prompt_limits(resolved_skills, config)

    remote_note = eligibility.remote.note.strip() if eligibility and eligibility.remote and eligibility.remote.note else ""
    trunc_note = f"[WARN] Skills truncated: included {len(skills_for_prompt)} of {len(resolved_skills)}." if truncated else ""

    prompt = "\n".join([p for p in [remote_note, trunc_note, format_skills_for_prompt(_compact_skill_paths(skills_for_prompt))] if p])
    return eligible, prompt, resolved_skills


def build_workspace_skills_prompt(
    workspace_dir: str,
    config: dict | None = None,
    entries: list[SkillEntry] | None = None,
    skill_filter: list[str] | None = None,
    eligibility: SkillEligibilityContext | None = None,
) -> str:
    return _resolve_prompt_state(workspace_dir, config, entries, skill_filter, eligibility)[1]


def build_workspace_skill_snapshot(
    workspace_dir: str,
    config: dict | None = None,
    entries: list[SkillEntry] | None = None,
    skill_filter: list[str] | None = None,
    eligibility: SkillEligibilityContext | None = None,
    snapshot_version: int | None = None,
) -> SkillSnapshot:
    eligible, prompt, resolved = _resolve_prompt_state(workspace_dir, config, entries, skill_filter, eligibility)
    return SkillSnapshot(
        prompt=prompt,
        skills=[
            SkillSnapshotSkill(
                name=e.skill.name,
                primary_env=e.metadata.primary_env if e.metadata else None,
                required_env=e.metadata.requires.env if e.metadata and e.metadata.requires else None,
            )
            for e in eligible
        ],
        skill_filter=normalize_skill_filter(skill_filter),
        resolved_skills=resolved,
        version=snapshot_version,
    )


def resolve_skills_prompt_for_run(
    workspace_dir: str,
    config: dict | None = None,
    skills_snapshot: SkillSnapshot | None = None,
    entries: list[SkillEntry] | None = None,
) -> str:
    if skills_snapshot and skills_snapshot.prompt.strip():
        return skills_snapshot.prompt
    if entries:
        return build_workspace_skills_prompt(workspace_dir, config, entries)
    return ""


def filter_workspace_skill_entries(entries: list[SkillEntry], config: dict | None = None) -> list[SkillEntry]:
    return _filter_skill_entries(entries, config)


def _sanitize_skill_command_name(raw: str) -> str:
    normalized = re.sub(r"[^a-z0-9_]+", "_", raw.lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return (normalized[:SKILL_COMMAND_MAX_LENGTH] or SKILL_COMMAND_FALLBACK)


def _resolve_unique_name(base: str, used: set[str]) -> str:
    if base.lower() not in used:
        return base
    for index in range(2, 1000):
        suffix = f"_{index}"
        max_base_len = max(1, SKILL_COMMAND_MAX_LENGTH - len(suffix))
        candidate = f"{base[:max_base_len]}{suffix}"
        if candidate.lower() not in used:
            return candidate
    return f"{base[:max(1, SKILL_COMMAND_MAX_LENGTH - 2)]}_x"


def build_workspace_skill_command_specs(
    workspace_dir: str,
    config: dict | None = None,
    managed_skills_dir: str | None = None,
    bundled_skills_dir: str | None = None,
    entries: list[SkillEntry] | None = None,
    skill_filter: list[str] | None = None,
    eligibility: SkillEligibilityContext | None = None,
    reserved_names: set[str] | None = None,
) -> list[SkillCommandSpec]:
    skill_entries = entries or load_workspace_skill_entries(workspace_dir, config, managed_skills_dir, bundled_skills_dir)
    eligible = _filter_skill_entries(skill_entries, config, skill_filter, eligibility)
    invocable = [e for e in eligible if not (e.invocation and not e.invocation.user_invocable)]

    used = {n.lower() for n in (reserved_names or set())}
    specs: list[SkillCommandSpec] = []

    for entry in invocable:
        base = _sanitize_skill_command_name(entry.skill.name)
        unique = _resolve_unique_name(base, used)
        used.add(unique.lower())

        raw_desc = entry.skill.description.strip() or entry.skill.name
        description = raw_desc if len(raw_desc) <= SKILL_COMMAND_DESCRIPTION_MAX_LENGTH else f"{raw_desc[:SKILL_COMMAND_DESCRIPTION_MAX_LENGTH - 1]}..."

        dispatch = None
        kind_raw = (entry.frontmatter.get("command-dispatch") or entry.frontmatter.get("command_dispatch") or "").strip().lower()
        if kind_raw == "tool":
            tool_name = (entry.frontmatter.get("command-tool") or entry.frontmatter.get("command_tool") or "").strip()
            if tool_name:
                dispatch = SkillCommandDispatchSpec(kind="tool", tool_name=tool_name, arg_mode="raw")

        specs.append(SkillCommandSpec(name=unique, skill_name=entry.skill.name, description=description, dispatch=dispatch))

    return specs


async def sync_skills_to_workspace(
    source_workspace_dir: str,
    target_workspace_dir: str,
    config: dict | None = None,
    managed_skills_dir: str | None = None,
    bundled_skills_dir: str | None = None,
) -> None:
    source_dir = Path(source_workspace_dir).expanduser().resolve()
    target_dir = Path(target_workspace_dir).expanduser().resolve()
    if source_dir == target_dir:
        return

    async def _do_sync():
        target_skills = target_dir / "skills"
        entries = load_workspace_skill_entries(str(source_dir), config, managed_skills_dir, bundled_skills_dir)

        if target_skills.exists():
            shutil.rmtree(target_skills, ignore_errors=True)
        target_skills.mkdir(parents=True, exist_ok=True)

        used_names: set[str] = set()
        for entry in entries:
            source_base = Path(entry.skill.base_dir)
            base_name = source_base.name.strip()
            if not base_name or base_name in {".", ".."}:
                continue

            destination_name = base_name
            index = 2
            while destination_name in used_names:
                destination_name = f"{base_name}-{index}"
                index += 1
            used_names.add(destination_name)

            destination = (target_skills / destination_name).resolve()
            try:
                shutil.copytree(source_base, destination, dirs_exist_ok=True)
            except OSError:
                continue

    await serialize_by_key(f"syncSkills:{target_dir}", _do_sync)
