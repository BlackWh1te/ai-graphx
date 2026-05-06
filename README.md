# Ai-GraphX

<p align="center">
  <a href="docs/translations/README.ru-RU.md"><img src="https://img.shields.io/badge/🇷🇺%20Русский-blue?style=for-the-badge" alt="Russian"></a>
</p>

**Ai-GraphX** is a knowledge graph tool that transforms your entire project — code, documentation, papers, images, and videos — into a navigable graph structure you can query instead of searching through files.

## What is Ai-GraphX?

Ai-GraphX analyzes your project files and builds a knowledge graph showing:
- **Entities and concepts** — functions, classes, variables, topics, ideas
- **Relationships** — how things connect (imports, calls, citations, references)
- **Communities** — clusters of related files and concepts
- **Cross-document connections** — links between code, docs, and papers you'd never think to ask about

Instead of grepping through hundreds of files, you ask questions and Ai-GraphX traverses the graph to find answers.

## Why use Ai-GraphX?

**For codebases you're new to:**
- See the architecture before touching anything
- Understand how modules connect
- Find the entry points and core components

**For research projects:**
- Build a citation graph from papers
- Connect concepts across multiple documents
- Trace how ideas evolve through your corpus

**For ongoing development:**
- Track what changed between commits
- See hot files (most frequently changed)
- Understand the impact of changes across the entire project

**Three things Ai-GraphX does that file search cannot:**
1. **Persistent graph** — relationships survive across sessions. Ask questions weeks later without re-reading everything.
2. **Honest audit trail** — every edge is tagged `EXTRACTED`, `INFERRED`, or `AMBIGUOUS`. You know what was found vs guessed.
3. **Cross-document surprise** — community detection finds connections between concepts in different files that you would never think to ask about directly.

---

Type `/graphx` in your AI coding assistant and it maps your entire project — code, docs, PDFs, images, videos — into a knowledge graph you can query instead of grepping through files.

Works in Claude Code, Devin, Cursor, Gemini CLI, GitHub Copilot CLI, VS Code Copilot Chat, Aider, OpenClaw, Factory Droid, Trae, Hermes, Kiro, Pi, and Google Antigravity.

```
/graphx .
```

That's it. You get three files:

```
graphx-out/
├── graph.html       open in any browser — click nodes, filter, search
├── GRAPH_REPORT.md  the highlights: key concepts, surprising connections, suggested questions
└── graph.json       the full graph — query it anytime without re-reading your files
```

---

## Install

**Requires Python 3.10+**

```bash
uv tool install ai-graphx && graphx install
# or: pipx install ai-graphx && graphx install
# or: pip install ai-graphx && graphx install
```

> **`graphx: command not found`?** Use `uv tool install ai-graphx` or `pipx install ai-graphx` — both put the CLI on PATH automatically. With plain `pip`, add `~/.local/bin` (Linux) or `~/Library/Python/3.x/bin` (Mac) to your PATH, or run `python -m graphx`.

### Pick your platform

| Platform | Install command |
|----------|----------------|
| Claude Code (Linux/Mac) | `graphx install` |
| Claude Code (Windows) | `graphx install --platform windows` |
| Codex | `graphx install --platform codex` |
| OpenCode | `graphx install --platform opencode` |
| GitHub Copilot CLI | `graphx install --platform copilot` |
| VS Code Copilot Chat | `graphx vscode install` |
| Aider | `graphx install --platform aider` |
| OpenClaw | `graphx install --platform claw` |
| Factory Droid | `graphx install --platform droid` |
| Trae | `graphx install --platform trae` |
| Trae CN | `graphx install --platform trae-cn` |
| Gemini CLI | `graphx install --platform gemini` |
| Hermes | `graphx install --platform hermes` |
| Kiro IDE/CLI | `graphx kiro install` |
| Pi coding agent | `graphx install --platform pi` |
| Cursor | `graphx cursor install` |
| Google Antigravity | `graphx antigravity install` |

> Codex users: also add `multi_agent = true` under `[features]` in `~/.codex/config.toml`.
> Codex uses `$graphx` instead of `/graphx`.

---

## Make your assistant always use the graph

Run this once in your project after building a graph:

| Platform | Command |
|----------|---------|
| Claude Code | `graphx claude install` |
| Codex | `graphx codex install` |
| OpenCode | `graphx opencode install` |
| GitHub Copilot CLI | `graphx copilot install` |
| VS Code Copilot Chat | `graphx vscode install` |
| Aider | `graphx aider install` |
| OpenClaw | `graphx claw install` |
| Factory Droid | `graphx droid install` |
| Trae | `graphx trae install` |
| Trae CN | `graphx trae-cn install` |
| Cursor | `graphx cursor install` |
| Gemini CLI | `graphx gemini install` |
| Hermes | `graphx hermes install` |
| Kiro IDE/CLI | `graphx kiro install` |
| Pi coding agent | `graphx pi install` |
| Google Antigravity | `graphx antigravity install` |

This writes a small config file that tells your assistant to read `GRAPH_REPORT.md` before answering questions about your codebase. On platforms that support hooks (Claude Code, Codex, Gemini CLI), a hook fires automatically before every file-read call — your assistant navigates by the graph instead of grepping through everything.

Uninstall with the matching command (e.g. `graphx claude uninstall`).

---

## What's in the report

- **God nodes** — the most-connected concepts in your project. Everything flows through these.
- **Surprising connections** — links between things that live in different files or modules. Ranked by how unexpected they are.
- **The "why"** — inline comments (`# NOTE:`, `# WHY:`, `# HACK:`), docstrings, and design rationale from docs are extracted as separate nodes linked to the code they explain.
- **Suggested questions** — 4–5 questions the graph is uniquely positioned to answer.
- **Confidence tags** — every inferred relationship is marked `EXTRACTED`, `INFERRED`, or `AMBIGUOUS`. You always know what was found vs guessed.

---

## What files it handles

| Type | Extensions |
|------|-----------|
| Code (25 languages) | `.py .ts .js .jsx .tsx .go .rs .java .c .cpp .rb .cs .kt .scala .php .swift .lua .zig .ps1 .ex .exs .m .jl .vue .svelte .sql` |
| Docs | `.md .mdx .html .txt .rst .yaml .yml` |
| Office | `.docx .xlsx` (requires `pip install ai-graphx[office]`) |
| PDFs | `.pdf` |
| Images | `.png .jpg .webp .gif` |
| Video / Audio | `.mp4 .mov .mp3 .wav` and more (requires `pip install ai-graphx[video]`) |
| YouTube / URLs | any video URL (requires `pip install ai-graphx[video]`) |

Code is extracted locally with no API calls (AST via tree-sitter). Everything else goes through your AI assistant's model API, unless you use local Ollama mode:

```bash
graphx ./my-project --ollama --model "llama3.2:3b"
```

Ollama mode writes the same `graphx-out/` files locally. It is useful for private/offline graph generation, but small local models usually produce weaker semantic relationships than `/graphx` inside a frontier-model assistant.

---

## Common commands

```bash
/graphx .                        # build graph for current folder
/graphx ./docs --update          # re-extract only changed files
/graphx . --cluster-only         # rerun clustering without re-extracting
/graphx . --no-viz               # skip the HTML, just the report + JSON
/graphx . --wiki                 # build a markdown wiki from the graph

graphx ./my-project --ollama --model "llama3.2:3b"  # local/private build with Ollama

/graphx query "what connects auth to the database?"
/graphx path "UserService" "DatabasePool"
/graphx explain "RateLimiter"

/graphx add https://arxiv.org/abs/1706.03762   # fetch a paper and add it
/graphx add <youtube-url>                       # transcribe and add a video

graphx hook install              # auto-rebuild on git commit
graphx merge-graphs a.json b.json              # combine two graphs
```

See the [full command reference](#full-command-reference) below.

---

## Ignoring files

Create a `.graphxignore` in your project root — same syntax as `.gitignore`, including `!` negation:

```
# .graphxignore
node_modules/
dist/
*.generated.py

# only index src/, ignore everything else
*
!src/
!src/**
```

---

## Team setup

`graphx-out/` is meant to be committed to git so everyone on the team starts with a map.

**Recommended `.gitignore` additions:**
```
graphx-out/manifest.json    # mtime-based, breaks after git clone
graphx-out/cost.json        # local only
# graphx-out/cache/         # optional: commit for speed, skip to keep repo small
```

**Workflow:**
1. One person runs `/graphx .` and commits `graphx-out/`.
2. Everyone pulls — their assistant reads the graph immediately.
3. Run `graphx hook install` to auto-rebuild after each commit (AST only, no API cost).
4. When docs or papers change, run `/graphx --update` to refresh those nodes.

---

## Using the graph directly

```bash
# query the graph from the terminal
graphx query "show the auth flow"
graphx query "what connects DigestAuth to Response?" --graph graphx-out/graph.json

# expose the graph as an MCP server (for repeated tool-call access)
python -m graphx.serve graphx-out/graph.json
```

The MCP server gives your assistant structured access: `query_graph`, `get_node`, `get_neighbors`, `shortest_path`.

> **WSL / Linux note:** Ubuntu ships `python3`, not `python`. Use a venv to avoid conflicts:
> ```bash
> python3 -m venv .venv && .venv/bin/pip install "ai-graphx[mcp]"
> ```

---

## Privacy

- **Code files** — processed locally via tree-sitter. Nothing leaves your machine.
- **Video / audio** — transcribed locally with faster-whisper. Nothing leaves your machine.
- **Docs, PDFs, images** — sent to your AI assistant's model API (Anthropic, OpenAI, etc.) using your own API key.
- No telemetry, no usage tracking, no analytics.

---

## Full command reference

```
/graphx                          # run on current directory
/graphx ./raw                    # run on a specific folder
/graphx ./raw --mode deep        # more aggressive relationship extraction
/graphx ./raw --update           # re-extract only changed files
/graphx ./raw --directed         # preserve edge direction
/graphx ./raw --cluster-only     # rerun clustering on existing graph
/graphx ./raw --no-viz           # skip HTML visualization
/graphx ./raw --obsidian         # generate Obsidian vault
/graphx ./raw --wiki             # build agent-crawlable markdown wiki
/graphx ./raw --svg              # export graph.svg
/graphx ./raw --graphml          # export for Gephi / yEd
/graphx ./raw --neo4j            # generate cypher.txt for Neo4j
/graphx ./raw --neo4j-push bolt://localhost:7687
/graphx ./raw --watch            # auto-sync as files change
/graphx ./raw --mcp              # start MCP stdio server

/graphx add https://arxiv.org/abs/1706.03762
/graphx add <video-url>
/graphx add https://... --author "Name" --contributor "Name"

/graphx query "what connects attention to the optimizer?"
/graphx query "..." --dfs --budget 1500
/graphx path "DigestAuth" "Response"
/graphx explain "SwinTransformer"

graphx hook install              # post-commit + post-checkout hooks
graphx hook uninstall
graphx hook status

graphx claude install / uninstall
graphx codex install / uninstall
graphx opencode install
graphx cursor install / uninstall
graphx gemini install / uninstall
graphx copilot install / uninstall
graphx aider install / uninstall
graphx claw install / uninstall
graphx droid install / uninstall
graphx trae install / uninstall
graphx trae-cn install / uninstall
graphx hermes install / uninstall
graphx kiro install / uninstall
graphx antigravity install / uninstall

graphx clone https://github.com/karpathy/nanoGPT
graphx merge-graphs a.json b.json --out merged.json
graphx watch ./src
graphx check-update ./src
graphx update ./src
graphx cluster-only ./my-project
```

---

## Learn more

- [How it works](docs/how-it-works.md) — the extraction pipeline, community detection, confidence scoring, benchmarks
- [ARCHITECTURE.md](ARCHITECTURE.md) — module breakdown, how to add a language
- [Optional integrations](docs/docker-mcp-sqlite.md) — Docker MCP Toolkit + SQLite

---

<details>
<summary>Contributing</summary>

**Worked examples** are the most useful contribution. Run `/graphx` on a real corpus, save the output to `worked/{slug}/`, write an honest `review.md` covering what the graph got right and wrong, and open a PR.

**Extraction bugs** — open an issue with the input file, the cache entry (`graphx-out/cache/`), and what was missed or wrong.

See [ARCHITECTURE.md](ARCHITECTURE.md) for module responsibilities and how to add a language.

</details>
