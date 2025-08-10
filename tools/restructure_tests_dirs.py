"""Utility script to (re)create the canonical tests/ directory base structure.

Actions performed:
1. Ensure tests/unit and tests/integration exist.
2. For each top-level module in src/, create matching subdirectory under both unit and integration with an __init__.py file.
3. Ensure __init__.py exists in tests/unit and tests/integration (but intentionally NOT recreating one at tests/ root per design request).
4. Leave existing legacy test folders (e.g. tests/common, tests/correos, etc.) untouched for later manual migration.

Idempotent: safe to run multiple times.
"""
from __future__ import annotations
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
TESTS_DIR = PROJECT_ROOT / "tests"
UNIT_DIR = TESTS_DIR / "unit"
INTEG_DIR = TESTS_DIR / "integration"

MODULE_DIRS = [
    d.name for d in SRC_DIR.iterdir()
    if d.is_dir() and not d.name.startswith('__')
]

# 1. Ensure base dirs
UNIT_DIR.mkdir(parents=True, exist_ok=True)
INTEG_DIR.mkdir(parents=True, exist_ok=True)

# 2. Create module subdirs with __init__.py
created = []
for base in (UNIT_DIR, INTEG_DIR):
    for mod in MODULE_DIRS:
        target = base / mod
        target.mkdir(exist_ok=True)
        init_file = target / "__init__.py"
        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")
        created.append(target)

# 3. Ensure __init__.py in unit & integration themselves
for d in (UNIT_DIR, INTEG_DIR):
    init_file = d / "__init__.py"
    if not init_file.exists():
        init_file.write_text("", encoding="utf-8")

print("Created/verified module directories:")
for p in sorted(created):
    print(f" - {p.relative_to(PROJECT_ROOT)}")

print("\nDone. Structure summary (first level under tests/):")
for d in sorted(p for p in TESTS_DIR.iterdir() if p.is_dir()):
    print(f" * {d.relative_to(PROJECT_ROOT)}")
