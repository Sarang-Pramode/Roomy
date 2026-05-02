# Changelog

All notable changes to **Roomy** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-05-02

### Added

- **`roomy dashboard`:** open the local web UI in a browser (`--host`, `--port`, `--path`); optional `--skip-check` to skip the dev-server port probe.
- **Optional extra `[examples]`:** `langgraph`, `langchain-openai`, `python-dotenv`, and `httpx` for the LangGraph + OpenAI example in the repository.
- **`GET /health`:** response now includes resolved **`db_path`** and **`session_count`** (useful for the inspector UI and debugging DB mismatches).

## [0.1.1] - 2026-04-30

### Changed

- **PyPI project page:** clearer `README` (install, quick start, extras, links).
- **Metadata:** `project.urls` now point at the GitHub repository and changelog.
- **Automation:** GitHub Actions workflow to publish to PyPI on **Release published** (Trusted Publishing).

## [0.1.0] - 2026-04-14

### Added

- Initial release on PyPI as **`roomy-observability`** (`import roomy`).
- SQLite tracing, LangChain callbacks, context segments, token estimates, CLI, FastAPI read API, diagnostics, sample agents, Docker.

[0.1.2]: https://github.com/Sarang-Pramode/Roomy/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/Sarang-Pramode/Roomy/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Sarang-Pramode/Roomy/releases/tag/v0.1.0
