# Changelog

<p align="center">
  <a href="docs/translations/CHANGELOG.ru-RU.md"><img src="https://img.shields.io/badge/🇷🇺%20Русский-blue?style=for-the-badge" alt="Russian"></a>
</p>

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.4] - 2026-05-05

### Added
- `graphx serve` command — starts a local server and automatically opens the `index.html` dashboard
- Comprehensive status detection — `graphx status` now detects and displays unstaged changes and untracked files

## [0.2.2] - 2026-05-05

### Added
- Live Activity Timeline — the dashboard now includes a "Current Session" section showing staged changes in real-time
- Staged Changes detection — `graphx status` and the dashboard now correctly identify and display files in the git index
- `/graphx-status` command — new explicit CLI trigger for the project health dashboard
- Automatic dashboard setup — `activity.json` and `index.html` are now automatically generated on the first run of `/graphx`

### Fixed
- Improved data model consistency across `activity.py`, `status.py`, and the dashboard
- Corrected GitPython diff logic to accurately report staged changes using `repo.index.diff("HEAD")`
- Added missing `size` field to staged changes in `activity.json` for dashboard compatibility

## [0.2.1] - 2026-05-05

### Added
- OpenCode `/graphx` custom command — `graphx install --platform opencode` now registers a global `/graphx` command in `~/.config/opencode/commands/graphx.md`
- `/graphx` command template executes `graphx $ARGUMENTS` — without args runs `graphx watch .`, with args passes them through (e.g., `/graphx status`, `/graphx query "..."`)

### Fixed
- `graphx opencode uninstall` now removes the `/graphx` command file alongside the plugin
- `skill-opencode.md` updated to document `/graphx` and `/graphx status`

## [0.2.0] - 2026-05-05

### Added
- Live activity tracking dashboard — `graphx-out/activity.json` is generated from git history with AI vs human commit detection
- Dynamic SPA `index.html` that polls `activity.json` every 30 seconds for real-time updates
- Activity timeline shows commit hash, author, timestamp, message, and file changes with A/M/D badges
- Git status section showing current branch, staged changes, untracked branches
- Hot files ranking, change velocity bar chart, merge commits, external files, large files
- New `activity.py` module with `_is_ai_commit()` heuristic for AI-authored commit detection
- `index.html` renders entirely from `window.INITIAL_DATA` with no build-time dependencies on page load

### Fixed
- `skill.md` updated to document live activity tracking capability

## [0.1.1] - 2026-04-04

### Added
- CI badge to README (GitHub Actions, Python 3.10 + 3.12)
- `ARCHITECTURE.md` — pipeline overview, module table, extraction schema, how to add a language
- `SECURITY.md` — threat model, mitigations, vulnerability reporting
- `worked/` directory with eval reports (karpathy-repos 71.5x benchmark, httpx, mixed-corpus)

### Fixed
- pytest not found in CI — added explicit `pip install pytest` step
- README test count (163 → 212), language table, worked examples links
- README reframed as Claude Code skill; Karpathy problem → graphx answer framing

## [0.1.0] - 2026-04-03

### Added
- Initial release
- 13-language AST extraction via tree-sitter (Python, JS, TS, Go, Rust, Java, C, C++, Ruby, C#, Kotlin, Scala, PHP)
- Leiden community detection via graspologic with oversized community splitting
- SHA256 semantic cache — warm re-runs skip unchanged files
- MCP stdio server — `query_graph`, `get_node`, `get_neighbors`, `shortest_path`, `god_nodes`
- Memory feedback loop — Q&A results saved to `graphx-out/memory/`, extracted on `--update`
- Obsidian vault export with wikilinks, community tags, Canvas layout
- Security module — URL validation, safe fetch with size cap, path guards, label sanitisation
- `graphx install` CLI — copies skill to `~/.claude/skills/` and registers in `CLAUDE.md`
- Parallel subagent extraction for docs, papers, and images
