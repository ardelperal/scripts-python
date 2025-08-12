# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning when versions are tagged. Until then, changes appear under Unreleased.

## [Unreleased]

### Changed
- Orchestrator: MasterRunner now executes daily and continuous tasks sequentially, mirroring the behavior of `SimpleMasterTaskRunner` for determinism and simpler debugging.
- Standardized logging and per-cycle summaries in `scripts/run_master.py`. During test dry-runs, script keys (e.g., "brass", "riesgos") are printed for visibility expected by tests.

### Removed
- Concurrency and threading in `MasterRunner` (removed `ThreadPoolExecutor` usage, `self.thread_lock`).
- Obsolete helpers: `ejecutar_script` and `_register_task_completion_for_script` and any related orphaned fragments.

### Added
- Test-focused fast-path: when `MASTER_DRY_SUBPROCESS=1` and single-cycle mode is enabled, `MasterRunner.run()` performs a lightweight cycle and exits quickly to avoid timeouts in CI.
- Helper utilities in `MasterRunner` to support configuration and scheduling: `_load_config`, `es_laborable` wrapper, `es_noche`, `get_tiempo_espera`, and `_update_cycle_context` placeholder.

### Docs
- `ARCHITECTURE.md`: Added a section describing the sequential execution model of the orchestrator and the test-only dry-run pathway.
