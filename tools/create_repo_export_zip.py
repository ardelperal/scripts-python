"""Utility to create a trimmed ZIP archive of the repository for LLM analysis.

Features:
  - Excludes virtual environments, caches, build artifacts, logs, large/local DB
    files (.accdb, .mdb, .laccdb), coverage outputs, and removed legacy assets.
  - Reads .gitignore (basic parsing) to extend exclusions (optional flag).
  - Provides --dry-run mode to list counts without writing the ZIP.
  - Allows overriding output path and adding extra exclude globs.
  - Keeps documentation, source code (src/), tests/, configuration, and examples.

Usage examples:
  python tools/create_repo_export_zip.py               # creates repo_export_YYYYMMDD_HHMM.zip in repo root
  python tools/create_repo_export_zip.py --output export.zip
  python tools/create_repo_export_zip.py --dry-run
  python tools/create_repo_export_zip.py --extra-exclude "examples/**" --dry-run

Notes:
  - Exclusion globs are matched against POSIX-style relative paths (e.g. "src/module/file.py").
  - Directory exclusions prevent descent (efficient skipping).
  - If you need to include Access DB schema docs (.md) they will still be included;
    only the binary DB files are excluded.
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import sys
import time
import zipfile
from collections.abc import Iterable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_EXCLUDES: list[str] = [
    # VCS / tooling
    ".git",
    ".git/**",
    ".idea",
    ".vscode",
    # Virtual envs
    "venv",
    "venv/**",
    ".venv",
    ".venv/**",
    "env",
    "env/**",
    "ENV",
    "ENV/**",
    # Python caches / compiled
    "__pycache__",
    "**/__pycache__",
    "*.py[cod]",
    "*.pyo",
    "*.pyd",
    "*.so",
    # Build / packaging artifacts
    "build",
    "dist",
    "downloads",
    "eggs",
    ".eggs",
    "*.egg-info",
    "*.egg",
    # Test / coverage artifacts
    ".tox",
    ".pytest_cache",
    ".pytest_cache/**",
    "htmlcov",
    "htmlcov/**",
    ".coverage*",
    "coverage.xml",
    "*.cover",
    # Logs
    "logs",
    "logs/**",
    "*.log",
    # Legacy removed quarantine
    "legacy/.removed",
    "legacy/.removed/**",
    # Local database / binary data files
    "*.accdb",
    "*.mdb",
    "*.laccdb",
    "dbs-locales/*.accdb",
    "dbs-locales/*.laccdb",
    # Misc OS / editor
    ".DS_Store",
    "Thumbs.db",
    "ehthumbs.db",
    # Debug / scratch artifacts referenced previously
    "debug_*.py",
    "verify_*.py",
    "debug_html",
    "debug_html/**",
    "quality_output.html",
    "setup_local_environment_root.log",
    # Generated exports (avoid nesting self)
    "repo_export_*.zip",
    "repo_export_*.tar.gz",
]


def load_gitignore_patterns(root: Path) -> list[str]:
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return []
    patterns: list[str] = []
    for line in gitignore.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("/"):
            line = line[1:]
        patterns.append(line)
    return patterns


def matches_any(path_rel: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(path_rel, pat) for pat in patterns)


def should_exclude(path: Path, rel_posix: str, patterns: Iterable[str]) -> bool:
    if matches_any(rel_posix, patterns):
        return True
    if path.is_dir() and matches_any(rel_posix.rstrip("/") + "/**", patterns):
        return True
    return False


def build_file_list(exclude_patterns: list[str]):
    included = []
    excluded = []
    for root, dirs, files in os.walk(REPO_ROOT, topdown=True):
        root_path = Path(root)
        # Prune dirs
        pruned_dirs = []
        for d in list(dirs):
            dir_path = root_path / d
            rel = dir_path.relative_to(REPO_ROOT).as_posix()
            if should_exclude(dir_path, rel, exclude_patterns):
                excluded.append(dir_path)
                continue
            pruned_dirs.append(d)
        dirs[:] = pruned_dirs
        for f in files:
            file_path = root_path / f
            rel = file_path.relative_to(REPO_ROOT).as_posix()
            if should_exclude(file_path, rel, exclude_patterns):
                excluded.append(file_path)
            else:
                included.append(file_path)
    return included, excluded


def create_zip(files: list[Path], output: Path) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            arcname = p.relative_to(REPO_ROOT).as_posix()
            zf.write(p, arcname=arcname)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a curated ZIP of the repository excluding non-relevant "
        "artifacts."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output zip file path (default: repo_export_YYYYMMDD_HHMM.zip in repo "
        "root)",
    )
    parser.add_argument(
        "--include-gitignore",
        action="store_true",
        help="Also parse .gitignore to extend exclusion patterns",
    )
    parser.add_argument(
        "--extra-exclude",
        action="append",
        default=[],
        help="Additional exclusion glob(s). Can be provided multiple times.",
    )
    parser.add_argument(
        "--force-include",
        action="append",
        default=[],
        help="Glob pattern(s) to force-include even if excluded. Can be repeated.",
    )
    parser.add_argument(
        "--list", action="store_true", help="List included file paths (verbose)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write the zip, only report statistics.",
    )
    parser.add_argument(
        "--show-excludes",
        action="store_true",
        help="Print the final exclusion pattern list.",
    )
    return parser.parse_args(argv)


def human_readable_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    patterns: list[str] = list(dict.fromkeys(DEFAULT_EXCLUDES))
    if args.include_gitignore:
        patterns.extend(load_gitignore_patterns(REPO_ROOT))
    if args.extra_exclude:
        patterns.extend(args.extra_exclude)
    patterns = [p[2:] if p.startswith("./") else p for p in patterns]
    if args.show_excludes:
        print(f"Exclusion patterns ({len(patterns)}):")
        for p in patterns:
            print("  -", p)
    included, excluded = build_file_list(patterns)
    # Force-include pass
    if args.force_include:
        force = args.force_include
        # Identify candidates among excluded paths (files only)
        readd = []
        for path in list(excluded):
            if path.is_dir():
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            if matches_any(rel, force):
                readd.append(path)
        if readd:
            for p in readd:
                excluded.remove(p)
                included.append(p)
            print(f"Force-included {len(readd)} file(s) overriding exclusion patterns.")
    timestamp = time.strftime("%Y%m%d_%H%M")
    default_name = f"repo_export_{timestamp}.zip"
    output_path = (args.output if args.output else (REPO_ROOT / default_name)).resolve()
    try:
        if output_path.is_relative_to(REPO_ROOT):  # type: ignore[attr-defined]
            included = [f for f in included if f.resolve() != output_path]
    except AttributeError:
        # Python <3.9 fallback not needed here but ensures compatibility
        if str(output_path).startswith(str(REPO_ROOT)):
            included = [f for f in included if f.resolve() != output_path]
    total_size = sum(f.stat().st_size for f in included)
    print(
        f"Included files: {len(included)}  | Excluded paths: {len(excluded)}  | "
        f"Total size: {human_readable_size(total_size)}"
    )
    if args.list:
        for f in included:
            print(" +", f.relative_to(REPO_ROOT).as_posix())
    if args.dry_run:
        print("Dry-run complete. No ZIP written.")
        return 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    create_zip(included, output_path)
    print(
        f"ZIP written: {output_path} (size: "
        f"{human_readable_size(output_path.stat().st_size)})
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
