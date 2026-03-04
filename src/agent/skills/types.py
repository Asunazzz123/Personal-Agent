from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class Skill:
    name: str
    description: str
    file_path: str
    base_dir: str
    source: str = ""


@dataclass(slots=True)
class SkillInstallSpec:
    kind: str
    id: str | None = None
    label: str | None = None
    bins: list[str] | None = None
    os: list[str] | None = None
    formula: str | None = None
    package: str | None = None
    module: str | None = None
    url: str | None = None
    archive: str | None = None
    extract: bool | None = None
    strip_components: int | None = None
    target_dir: str | None = None


@dataclass(slots=True)
class SkillRequires:
    bins: list[str] | None = None
    any_bins: list[str] | None = None
    env: list[str] | None = None
    config: list[str] | None = None


@dataclass(slots=True)
class OpenClawSkillMetadata:
    always: bool | None = None
    skill_key: str | None = None
    primary_env: str | None = None
    emoji: str | None = None
    homepage: str | None = None
    os: list[str] | None = None
    requires: SkillRequires | None = None
    install: list[SkillInstallSpec] | None = None


@dataclass(slots=True)
class SkillInvocationPolicy:
    user_invocable: bool = True
    disable_model_invocation: bool = False


@dataclass(slots=True)
class SkillCommandDispatchSpec:
    kind: str
    tool_name: str
    arg_mode: str = "raw"


@dataclass(slots=True)
class SkillCommandSpec:
    name: str
    skill_name: str
    description: str
    dispatch: SkillCommandDispatchSpec | None = None


@dataclass(slots=True)
class RemoteEligibility:
    platforms: list[str]
    has_bin: Callable[[str], bool]
    has_any_bin: Callable[[list[str]], bool]
    note: str | None = None


@dataclass(slots=True)
class SkillEligibilityContext:
    remote: RemoteEligibility | None = None


ParsedSkillFrontmatter = dict[str, str]


@dataclass(slots=True)
class SkillEntry:
    skill: Skill
    frontmatter: ParsedSkillFrontmatter = field(default_factory=dict)
    metadata: OpenClawSkillMetadata | None = None
    invocation: SkillInvocationPolicy | None = None


@dataclass(slots=True)
class SkillSnapshotSkill:
    name: str
    primary_env: str | None = None
    required_env: list[str] | None = None


@dataclass(slots=True)
class SkillSnapshot:
    prompt: str
    skills: list[SkillSnapshotSkill]
    skill_filter: list[str] | None = None
    resolved_skills: list[Skill] | None = None
    version: int | None = None


OpenClawConfig = dict[str, Any]
