from __future__ import annotations

import json
import re
from urllib.parse import urlparse

from .types import (
    OpenClawSkillMetadata,
    ParsedSkillFrontmatter,
    SkillInstallSpec,
    SkillInvocationPolicy,
    SkillRequires,
    Skill,
    SkillEntry,
)

BREW_FORMULA_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9@+._/-]*$")
GO_MODULE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._~+\-/]*(?:@[A-Za-z0-9][A-Za-z0-9._~+\-/]*)?$")
UV_PACKAGE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-[\]=<>!~+,]*$")


def parse_frontmatter(content: str) -> ParsedSkillFrontmatter:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    result: ParsedSkillFrontmatter = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def _normalize_bool(value: str | None, fallback: bool) -> bool:
    if value is None:
        return fallback
    text = value.strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return fallback


def _normalize_string_list(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(v).strip() for v in raw if str(v).strip()]


def _safe_brew_formula(raw: object) -> str | None:
    if not isinstance(raw, str):
        return None
    formula = raw.strip()
    if not formula or formula.startswith("-") or "\\" in formula or ".." in formula:
        return None
    if not BREW_FORMULA_PATTERN.match(formula):
        return None
    return formula


def _safe_npm_spec(raw: object) -> str | None:
    if not isinstance(raw, str):
        return None
    spec = raw.strip()
    if not spec or spec.startswith("-"):
        return None
    if spec.startswith("file:") or spec.startswith("link:"):
        return None
    return spec


def _safe_go_module(raw: object) -> str | None:
    if not isinstance(raw, str):
        return None
    module_spec = raw.strip()
    if not module_spec or module_spec.startswith("-") or "\\" in module_spec or "://" in module_spec:
        return None
    if not GO_MODULE_PATTERN.match(module_spec):
        return None
    return module_spec


def _safe_uv_package(raw: object) -> str | None:
    if not isinstance(raw, str):
        return None
    pkg = raw.strip()
    if not pkg or pkg.startswith("-") or "\\" in pkg or "://" in pkg:
        return None
    if not UV_PACKAGE_PATTERN.match(pkg):
        return None
    return pkg


def _safe_download_url(raw: object) -> str | None:
    if not isinstance(raw, str):
        return None
    value = raw.strip()
    if not value or re.search(r"\s", value):
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return None
    return value


def _parse_install_spec(raw: object) -> SkillInstallSpec | None:
    if not isinstance(raw, dict):
        return None
    kind = str(raw.get("kind", "")).strip()
    if kind not in {"brew", "node", "go", "uv", "download"}:
        return None

    spec = SkillInstallSpec(kind=kind)
    if isinstance(raw.get("id"), str):
        spec.id = raw["id"].strip() or None
    if isinstance(raw.get("label"), str):
        spec.label = raw["label"].strip() or None
    bins = _normalize_string_list(raw.get("bins"))
    if bins:
        spec.bins = bins
    os_list = _normalize_string_list(raw.get("os"))
    if os_list:
        spec.os = os_list

    spec.formula = _safe_brew_formula(raw.get("formula")) or _safe_brew_formula(raw.get("cask"))
    if kind == "node":
        spec.package = _safe_npm_spec(raw.get("package"))
    if kind == "uv":
        spec.package = _safe_uv_package(raw.get("package"))
    spec.module = _safe_go_module(raw.get("module"))
    spec.url = _safe_download_url(raw.get("url"))

    if isinstance(raw.get("archive"), str):
        spec.archive = raw["archive"]
    if isinstance(raw.get("extract"), bool):
        spec.extract = raw["extract"]
    if isinstance(raw.get("stripComponents"), int):
        spec.strip_components = raw["stripComponents"]
    if isinstance(raw.get("targetDir"), str):
        spec.target_dir = raw["targetDir"]

    if kind == "brew" and not spec.formula:
        return None
    if kind == "node" and not spec.package:
        return None
    if kind == "go" and not spec.module:
        return None
    if kind == "uv" and not spec.package:
        return None
    if kind == "download" and not spec.url:
        return None

    return spec


def resolve_openclaw_metadata(frontmatter: ParsedSkillFrontmatter) -> OpenClawSkillMetadata | None:
    raw_metadata = frontmatter.get("metadata")
    if not raw_metadata:
        return None
    try:
        metadata_obj = json.loads(raw_metadata)
    except json.JSONDecodeError:
        return None

    openclaw = metadata_obj.get("openclaw") if isinstance(metadata_obj, dict) else None
    if not isinstance(openclaw, dict):
        return None

    requires_obj = openclaw.get("requires") if isinstance(openclaw.get("requires"), dict) else None
    requires = None
    if requires_obj:
        requires = SkillRequires(
            bins=_normalize_string_list(requires_obj.get("bins")) or None,
            any_bins=_normalize_string_list(requires_obj.get("anyBins")) or None,
            env=_normalize_string_list(requires_obj.get("env")) or None,
            config=_normalize_string_list(requires_obj.get("config")) or None,
        )

    install_specs: list[SkillInstallSpec] = []
    if isinstance(openclaw.get("install"), list):
        for item in openclaw["install"]:
            parsed = _parse_install_spec(item)
            if parsed is not None:
                install_specs.append(parsed)

    os_list = _normalize_string_list(openclaw.get("os"))
    return OpenClawSkillMetadata(
        always=openclaw.get("always") if isinstance(openclaw.get("always"), bool) else None,
        skill_key=openclaw.get("skillKey") if isinstance(openclaw.get("skillKey"), str) else None,
        primary_env=openclaw.get("primaryEnv") if isinstance(openclaw.get("primaryEnv"), str) else None,
        emoji=openclaw.get("emoji") if isinstance(openclaw.get("emoji"), str) else None,
        homepage=openclaw.get("homepage") if isinstance(openclaw.get("homepage"), str) else None,
        os=os_list or None,
        requires=requires,
        install=install_specs or None,
    )


def resolve_skill_invocation_policy(frontmatter: ParsedSkillFrontmatter) -> SkillInvocationPolicy:
    return SkillInvocationPolicy(
        user_invocable=_normalize_bool(frontmatter.get("user-invocable"), True),
        disable_model_invocation=_normalize_bool(frontmatter.get("disable-model-invocation"), False),
    )


def resolve_skill_key(skill: Skill, entry: SkillEntry | None = None) -> str:
    if entry and entry.metadata and entry.metadata.skill_key:
        return entry.metadata.skill_key
    return skill.name
