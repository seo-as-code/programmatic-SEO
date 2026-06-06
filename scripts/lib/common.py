from __future__ import annotations

import glob
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = BASE_DIR / "config"


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_yaml(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / name
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_project_config() -> dict[str, Any]:
    cfg = load_yaml("project.yaml")
    local_path = CONFIG_DIR / "project.local.yaml"
    if local_path.exists():
        with local_path.open(encoding="utf-8") as f:
            local = yaml.safe_load(f) or {}
        cfg = _deep_merge(cfg, local)
    return cfg


def load_patterns_config() -> dict[str, Any]:
    cfg = load_yaml("patterns.yaml")
    local_path = CONFIG_DIR / "patterns.local.yaml"
    if local_path.exists():
        with local_path.open(encoding="utf-8") as f:
            local = yaml.safe_load(f) or {}
        cfg = _deep_merge(cfg, local)
    return cfg


def site_origin(project: dict[str, Any] | None = None) -> str:
    proj = project or load_project_config()
    origin = proj.get("project", {}).get("origin", "")
    if not origin:
        raise ValueError("Define project.origin in config/project.yaml or project.local.yaml")
    return origin.rstrip("/")


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def latest_file(pattern: str) -> str | None:
    files = sorted(glob.glob(pattern), key=os.path.getmtime)
    return files[-1] if files else None


def resolve_data_path(project: dict[str, Any], key: str, fallback: str) -> str:
    sources = project.get("data_sources", {})
    rel = sources.get(key, fallback)
    path = BASE_DIR / rel
    return str(path)
