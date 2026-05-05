"""graphx CLI - `graphx install` sets up the Claude Code skill."""
from __future__ import annotations
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from graphx import __version__ as _graphx_version
    __version__ = _graphx_version
except:
    __version__ = "0.1.0"

# Output directory — override with GRAPHX_OUT env var for worktrees or shared-output setups.
# Accepts a relative name ("graphx-out-feature") or an absolute path ("/shared/graphx-out").
_GRAPHX_OUT = os.environ.get("GRAPHX_OUT", "graphx-out")


def _check_skill_version(skill_dst: Path) -> None:
    """Warn if the installed skill is from an older graphx version."""
    version_file = skill_dst.parent / ".graphx_version"
    if not version_file.exists():
        return
    installed = version_file.read_text(encoding="utf-8").strip()
    if installed != __version__:
        print(f"  warning: skill is from graphx {installed}, package is {__version__}. Run 'graphx install' to update.")


def _refresh_all_version_stamps() -> None:
    """After a successful install, update .graphx_version in all other known skill dirs.

    Prevents stale-version warnings from platforms that were installed previously
    but not explicitly re-installed during this upgrade.
    """
    for cfg in _PLATFORM_CONFIG.values():
        vf = Path.home() / cfg["skill_dst"]
        vf = vf.parent / ".graphx_version"
        if vf.exists():
            vf.write_text(__version__, encoding="utf-8")

_SETTINGS_HOOK = {
    # Claude Code v2.1.117+ removed dedicated Grep/Glob tools; searches now go through Bash.
    # We match on Bash and inspect the command string to avoid firing on every shell call.
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": (
                "CMD=$(python3 -c \""
                "import json,sys; d=json.load(sys.stdin); "
                "print(d.get('tool_input',d).get('command',''))\" 2>/dev/null || true); "
                "case \"$CMD\" in "
                r"*grep*|*rg\ *|*ripgrep*|*find\ *|*fd\ *|*ack\ *|*ag\ *) "
                "  [ -f graphx-out/graph.json ] && "
                r"""  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"graphx: Knowledge graph exists. Read graphx-out/GRAPH_REPORT.md for god nodes and community structure before searching raw files."}}' """
                "  || true ;; "
                "esac"
            ),
        }
    ],
}

_SKILL_REGISTRATION = (
    "\n# graphx\n"
    "- **graphx** (`~/.claude/skills/graphx/SKILL.md`) "
    "- any input to knowledge graph. Trigger: `/graphx`\n"
    "When the user types `/graphx`, invoke the Skill tool "
    "with `skill: \"graphx\"` before doing anything else.\n"
)


_PLATFORM_CONFIG: dict[str, dict] = {
    "claude": {
        "skill_file": "skill.md",
        "skill_dst": Path(".claude") / "skills" / "graphx" / "SKILL.md",
        "claude_md": True,
        "detect_dir": Path(".claude"),
    },
    "codex": {
        "skill_file": "skill-codex.md",
        "skill_dst": Path(".agents") / "skills" / "graphx" / "SKILL.md",
        "claude_md": False,
        "detect_dir": Path(".agents"),
    },
    "opencode": {
        "skill_file": "skill-opencode.md",
        "skill_dst": Path(".config") / "opencode" / "skills" / "graphx" / "SKILL.md",
        "claude_md": False,
        "detect_dir": Path(".config") / "opencode",
    },
    "aider": {
        "skill_file": "skill-aider.md",
        "skill_dst": Path(".aider") / "graphx" / "SKILL.md",
        "claude_md": False,
        "detect_dir": Path(".aider"),
    },
    "copilot": {
        "skill_file": "skill-copilot.md",
        "skill_dst": Path(".copilot") / "skills" / "graphx" / "SKILL.md",
        "claude_md": False,
        "detect_dir": Path(".copilot"),
    },
    "claw": {
        "skill_file": "skill-claw.md",
        "skill_dst": Path(".openclaw") / "skills" / "graphx" / "SKILL.md",
        "claude_md": False,
        "detect_dir": Path(".openclaw"),
    },
    "droid": {
        "skill_file": "skill-droid.md",
        "skill_dst": Path(".factory") / "skills" / "graphx" / "SKILL.md",
        "claude_md": False,
        "detect_dir": Path(".factory"),
    },
    "trae": {
        "skill_file": "skill-trae.md",
        "skill_dst": Path(".trae") / "skills" / "graphx" / "SKILL.md",
        "claude_md": False,
        "detect_dir": Path(".trae"),
    },
    "trae-cn": {
        "skill_file": "skill-trae.md",
        "skill_dst": Path(".trae-cn") / "skills" / "graphx" / "SKILL.md",
        "claude_md": False,
        "detect_dir": Path(".trae-cn"),
    },
    "hermes": {
        "skill_file": "skill-claw.md",
        "skill_dst": Path(".hermes") / "skills" / "graphx" / "SKILL.md",
        "claude_md": False,
        "detect_dir": Path(".hermes"),
    },
    "kiro": {
        "skill_file": "skill-kiro.md",
        "skill_dst": Path(".kiro") / "skills" / "graphx" / "SKILL.md",
        "claude_md": False,
        "detect_dir": Path(".kiro"),
    },
    "pi": {
        "skill_file": "skill-pi.md",
        "skill_dst": Path(".pi") / "agent" / "skills" / "graphx" / "SKILL.md",
        "claude_md": False,
        "detect_dir": Path(".pi"),
    },
    "antigravity": {
        "skill_file": "skill.md",
        "skill_dst": Path(".agents") / "skills" / "graphx" / "SKILL.md",
        "claude_md": False,
        "detect_dir": Path(".agents"),
    },
    "windows": {
        "skill_file": "skill-windows.md",
        "skill_dst": Path(".claude") / "skills" / "graphx" / "SKILL.md",
        "claude_md": True,
        "detect_dir": Path(".claude"),
    },
}


def _detect_installed_platforms() -> list[str]:
    """Scan home directory for known AI assistant config directories.

    Returns a deduplicated list of platform names whose config directories
    exist. Conflicts (e.g. claude vs windows both use ~/.claude) are
    resolved by OS preference.
    """
    home = Path.home()
    detected: list[str] = []
    seen_dirs: set[Path] = set()

    # Platforms that have their own dedicated install functions (checked separately)
    special_platforms = {"gemini", "cursor", "vscode"}

    for name, cfg in _PLATFORM_CONFIG.items():
        detect_dir = cfg.get("detect_dir")
        if not detect_dir:
            continue
        abs_dir = home / detect_dir
        if not abs_dir.exists():
            continue
        # Resolve conflicts: same detect_dir used by multiple platforms
        if detect_dir in seen_dirs:
            # claude vs windows: pick based on OS
            if name == "windows" and platform.system() == "Windows":
                # Replace claude with windows on Windows
                if "claude" in detected:
                    detected = [p for p in detected if p != "claude"]
                    detected.append(name)
            elif name == "claude" and platform.system() != "Windows":
                # Prefer claude on non-Windows (already there, skip windows)
                pass
            # codex vs antigravity: prefer codex (more common)
            elif name == "codex" and "antigravity" in detected:
                detected = [p for p in detected if p != "antigravity"]
                detected.append(name)
            elif name == "antigravity" and "codex" in detected:
                pass  # keep codex
            continue
        seen_dirs.add(detect_dir)
        detected.append(name)

    # Also check special platforms that use their own install functions
    # Cursor
    if (home / ".cursor").exists() and "cursor" not in detected:
        detected.append("cursor")
    # Gemini
    if platform.system() == "Windows":
        if (home / ".agents" / "skills").exists() and "gemini" not in detected:
            detected.append("gemini")
    else:
        if (home / ".gemini").exists() and "gemini" not in detected:
            detected.append("gemini")
    # Devin
    devin_config = (
        Path(os.environ.get("APPDATA", "")) / "devin" / "config.json"
        if platform.system() == "Windows"
        else home / ".config" / "devin" / "config.json"
    )
    if devin_config.exists() and "devin" not in detected:
        detected.append("devin")

    return detected


def _install_single(platform: str) -> bool:
    """Install to one platform. Returns True on success, prints its own errors."""
    if platform == "gemini":
        gemini_install()
        return True
    if platform == "cursor":
        _cursor_install(Path("."))
        return True
    if platform == "devin":
        _devin_install()
        return True
    if platform not in _PLATFORM_CONFIG:
        print(
            f"error: unknown platform '{platform}'. Choose from: {', '.join(_PLATFORM_CONFIG)}, gemini, cursor, devin",
            file=sys.stderr,
        )
        return False

    cfg = _PLATFORM_CONFIG[platform]
    skill_src = Path(__file__).parent / cfg["skill_file"]
    if not skill_src.exists():
        print(f"error: {cfg['skill_file']} not found in package - reinstall graphx", file=sys.stderr)
        return False

    import os as _os
    if platform in ("claude", "windows") and _os.environ.get("CLAUDE_CONFIG_DIR"):
        _claude_base = Path(_os.environ["CLAUDE_CONFIG_DIR"])
        skill_dst = _claude_base / "skills" / "graphx" / "SKILL.md"
    else:
        skill_dst = Path.home() / cfg["skill_dst"]
    skill_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(skill_src, skill_dst)
    (skill_dst.parent / ".graphx_version").write_text(__version__, encoding="utf-8")
    print(f"  skill installed  ->  {skill_dst}")

    if cfg["claude_md"]:
        claude_md = Path.home() / ".claude" / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text(encoding="utf-8")
            if "graphx" in content:
                print(f"  CLAUDE.md        ->  already registered (no change)")
            else:
                claude_md.write_text(content.rstrip() + _SKILL_REGISTRATION, encoding="utf-8")
                print(f"  CLAUDE.md        ->  skill registered in {claude_md}")
        else:
            claude_md.parent.mkdir(parents=True, exist_ok=True)
            claude_md.write_text(_SKILL_REGISTRATION.lstrip(), encoding="utf-8")
            print(f"  CLAUDE.md        ->  created at {claude_md}")

    if platform == "opencode":
        _install_opencode_plugin(Path("."))

    return True


def install(platform: str = "claude") -> None:
    """Install to a single platform (legacy entry point)."""
    if platform == "gemini":
        gemini_install()
        return
    if platform == "cursor":
        _cursor_install(Path("."))
        return
    if platform not in _PLATFORM_CONFIG:
        print(
            f"error: unknown platform '{platform}'. Choose from: {', '.join(_PLATFORM_CONFIG)}, gemini, cursor, devin",
            file=sys.stderr,
        )
        sys.exit(1)

    cfg = _PLATFORM_CONFIG[platform]
    skill_src = Path(__file__).parent / cfg["skill_file"]
    if not skill_src.exists():
        print(f"error: {cfg['skill_file']} not found in package - reinstall graphx", file=sys.stderr)
        sys.exit(1)

    import os as _os
    if platform in ("claude", "windows") and _os.environ.get("CLAUDE_CONFIG_DIR"):
        _claude_base = Path(_os.environ["CLAUDE_CONFIG_DIR"])
        skill_dst = _claude_base / "skills" / "graphx" / "SKILL.md"
    else:
        skill_dst = Path.home() / cfg["skill_dst"]
    skill_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(skill_src, skill_dst)
    (skill_dst.parent / ".graphx_version").write_text(__version__, encoding="utf-8")
    print(f"  skill installed  ->  {skill_dst}")

    if cfg["claude_md"]:
        # Register in ~/.claude/CLAUDE.md (Claude Code only)
        claude_md = Path.home() / ".claude" / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text(encoding="utf-8")
            if "graphx" in content:
                print(f"  CLAUDE.md        ->  already registered (no change)")
            else:
                claude_md.write_text(content.rstrip() + _SKILL_REGISTRATION, encoding="utf-8")
                print(f"  CLAUDE.md        ->  skill registered in {claude_md}")
        else:
            claude_md.parent.mkdir(parents=True, exist_ok=True)
            claude_md.write_text(_SKILL_REGISTRATION.lstrip(), encoding="utf-8")
            print(f"  CLAUDE.md        ->  created at {claude_md}")

    if platform == "opencode":
        _install_opencode_plugin(Path("."))

    # Refresh version stamps in all other previously-installed skill dirs so
    # stale-version warnings don't fire for platforms not explicitly re-installed.
    _refresh_all_version_stamps()

    print()
    print("Done. Open your AI coding assistant and type:")
    print()
    print("  /graphx .")
    print()


_CLAUDE_MD_SECTION = """\
## graphx

This project has a graphx knowledge graph at graphx-out/.

Rules:
- Before answering architecture or codebase questions, read graphx-out/GRAPH_REPORT.md for god nodes and community structure
- If graphx-out/wiki/index.md exists, navigate it instead of reading raw files
- For cross-module "how does X relate to Y" questions, prefer `graphx query "<question>"`, `graphx path "<A>" "<B>"`, or `graphx explain "<concept>"` over grep — these traverse the graph's EXTRACTED + INFERRED edges instead of scanning files
- After modifying code files in this session, run `graphx update .` to keep the graph current (AST-only, no API cost)
- To pull latest changes from git before updating, run `graphx update . --pull`
"""

_CLAUDE_MD_MARKER = "## graphx"

# AGENTS.md section for Codex, OpenCode, and OpenClaw.
# All three platforms read AGENTS.md in the project root for persistent instructions.
_AGENTS_MD_SECTION = """\
## graphx

This project has a graphx knowledge graph at graphx-out/.

Rules:
- Before answering architecture or codebase questions, read graphx-out/GRAPH_REPORT.md for god nodes and community structure
- If graphx-out/wiki/index.md exists, navigate it instead of reading raw files
- For cross-module "how does X relate to Y" questions, prefer `graphx query "<question>"`, `graphx path "<A>" "<B>"`, or `graphx explain "<concept>"` over grep — these traverse the graph's EXTRACTED + INFERRED edges instead of scanning files
- After modifying code files in this session, run `graphx update .` to keep the graph current (AST-only, no API cost)
- To pull latest changes from git before updating, run `graphx update . --pull`
"""

_AGENTS_MD_MARKER = "## graphx"

_GEMINI_MD_SECTION = """\
## graphx

This project has a graphx knowledge graph at graphx-out/.

Rules:
- Before answering architecture or codebase questions, read graphx-out/GRAPH_REPORT.md for god nodes and community structure
- If graphx-out/wiki/index.md exists, navigate it instead of reading raw files
- For cross-module "how does X relate to Y" questions, prefer `graphx query "<question>"`, `graphx path "<A>" "<B>"`, or `graphx explain "<concept>"` over grep — these traverse the graph's EXTRACTED + INFERRED edges instead of scanning files
- After modifying code files in this session, run `graphx update .` to keep the graph current (AST-only, no API cost)
- To pull latest changes from git before updating, run `graphx update . --pull`
"""

_GEMINI_MD_MARKER = "## graphx"

_GEMINI_HOOK = {
    "matcher": "read_file|list_directory",
    "hooks": [
        {
            "type": "command",
            "command": (
                'python -c "'
                "import sys,pathlib,json;"
                "e=pathlib.Path('graphx-out/graph.json').exists();"
                "d={'decision':'allow'};"
                "e and d.update({'additionalContext':'graphx: Knowledge graph exists. Read graphx-out/GRAPH_REPORT.md for god nodes and community structure before searching raw files.'});"
                "sys.stdout.write(json.dumps(d))"
                '"'
            ),
        }
    ],
}


def gemini_install(project_dir: Path | None = None) -> None:
    """Copy skill file to ~/.gemini/skills/graphx/, write GEMINI.md section, and install BeforeTool hook."""
    # Copy skill file to ~/.gemini/skills/graphx/SKILL.md
    # On Windows, Gemini CLI prioritises ~/.agents/skills/ over ~/.gemini/skills/
    skill_src = Path(__file__).parent / "skill.md"
    if platform.system() == "Windows":
        skill_dst = Path.home() / ".agents" / "skills" / "graphx" / "SKILL.md"
    else:
        skill_dst = Path.home() / ".gemini" / "skills" / "graphx" / "SKILL.md"
    skill_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(skill_src, skill_dst)
    (skill_dst.parent / ".graphx_version").write_text(__version__, encoding="utf-8")
    print(f"  skill installed  ->  {skill_dst}")

    target = (project_dir or Path(".")) / "GEMINI.md"

    if target.exists():
        content = target.read_text(encoding="utf-8")
        if _GEMINI_MD_MARKER in content:
            print("graphx already configured in GEMINI.md")
        else:
            target.write_text(content.rstrip() + "\n\n" + _GEMINI_MD_SECTION, encoding="utf-8")
            print(f"graphx section written to {target.resolve()}")
    else:
        target.write_text(_GEMINI_MD_SECTION, encoding="utf-8")
        print(f"graphx section written to {target.resolve()}")

    _install_gemini_hook(project_dir or Path("."))
    print()
    print("Gemini CLI will now check the knowledge graph before answering")
    print("codebase questions and rebuild it after code changes.")


def _install_gemini_hook(project_dir: Path) -> None:
    settings_path = project_dir / ".gemini" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    except json.JSONDecodeError:
        settings = {}
    before_tool = settings.setdefault("hooks", {}).setdefault("BeforeTool", [])
    settings["hooks"]["BeforeTool"] = [h for h in before_tool if "graphx" not in str(h)]
    settings["hooks"]["BeforeTool"].append(_GEMINI_HOOK)
    settings_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    print("  .gemini/settings.json  ->  BeforeTool hook registered")


def _uninstall_gemini_hook(project_dir: Path) -> None:
    settings_path = project_dir / ".gemini" / "settings.json"
    if not settings_path.exists():
        return
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    before_tool = settings.get("hooks", {}).get("BeforeTool", [])
    filtered = [h for h in before_tool if "graphx" not in str(h)]
    if len(filtered) == len(before_tool):
        return
    settings["hooks"]["BeforeTool"] = filtered
    settings_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    print("  .gemini/settings.json  ->  BeforeTool hook removed")


def gemini_uninstall(project_dir: Path | None = None) -> None:
    """Remove the graphx section from GEMINI.md, uninstall hook, and remove skill file."""
    # Remove skill file (mirror the install path detection)
    if platform.system() == "Windows":
        skill_dst = Path.home() / ".agents" / "skills" / "graphx" / "SKILL.md"
    else:
        skill_dst = Path.home() / ".gemini" / "skills" / "graphx" / "SKILL.md"
    if skill_dst.exists():
        skill_dst.unlink()
        print(f"  skill removed    ->  {skill_dst}")
    version_file = skill_dst.parent / ".graphx_version"
    if version_file.exists():
        version_file.unlink()
    for d in (skill_dst.parent, skill_dst.parent.parent):
        try:
            d.rmdir()
        except OSError:
            break

    target = (project_dir or Path(".")) / "GEMINI.md"
    if not target.exists():
        print("No GEMINI.md found in current directory - nothing to do")
        return
    content = target.read_text(encoding="utf-8")
    if _GEMINI_MD_MARKER not in content:
        print("graphx section not found in GEMINI.md - nothing to do")
        return
    cleaned = re.sub(r"\n*## graphx\n.*?(?=\n## |\Z)", "", content, flags=re.DOTALL).rstrip()
    if cleaned:
        target.write_text(cleaned + "\n", encoding="utf-8")
        print(f"graphx section removed from {target.resolve()}")
    else:
        target.unlink()
        print(f"GEMINI.md was empty after removal - deleted {target.resolve()}")
    _uninstall_gemini_hook(project_dir or Path("."))


_VSCODE_INSTRUCTIONS_MARKER = "## graphx"
_VSCODE_INSTRUCTIONS_SECTION = """\
## graphx

For any question about this repo's architecture, structure, components, or how to add/modify/find
code, your **first tool call must be** to read `graphx-out/GRAPH_REPORT.md` (if it exists).

Triggers: "how do I…", "where is…", "what does … do", "add/modify a <component>",
"explain the architecture", or anything that depends on how files or classes relate.

After reading the report (and `graphx-out/wiki/index.md` for deep questions), answer from the
graph. Only read source files when (a) modifying/debugging specific code, (b) the graph lacks
the needed detail, or (c) the graph is missing or stale.

Type `/graphx` in Copilot Chat to build or update the graph.
"""


def vscode_install(project_dir: Path | None = None) -> None:
    """Install graphx skill for VS Code Copilot Chat + write .github/copilot-instructions.md."""
    skill_src = Path(__file__).parent / "skill-vscode.md"
    if not skill_src.exists():
        skill_src = Path(__file__).parent / "skill-copilot.md"
    skill_dst = Path.home() / ".copilot" / "skills" / "graphx" / "SKILL.md"
    skill_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(skill_src, skill_dst)
    (skill_dst.parent / ".graphx_version").write_text(__version__, encoding="utf-8")
    print(f"  skill installed  ->  {skill_dst}")

    instructions = (project_dir or Path(".")) / ".github" / "copilot-instructions.md"
    instructions.parent.mkdir(parents=True, exist_ok=True)
    if instructions.exists():
        content = instructions.read_text(encoding="utf-8")
        if _VSCODE_INSTRUCTIONS_MARKER in content:
            print(f"  {instructions}  ->  already configured (no change)")
        else:
            instructions.write_text(content.rstrip() + "\n\n" + _VSCODE_INSTRUCTIONS_SECTION, encoding="utf-8")
            print(f"  {instructions}  ->  graphx section added")
    else:
        instructions.write_text(_VSCODE_INSTRUCTIONS_SECTION, encoding="utf-8")
        print(f"  {instructions}  ->  created")

    print()
    print("VS Code Copilot Chat configured. Type /graphx in the chat panel to build the graph.")
    print("Note: for GitHub Copilot CLI (terminal), use: graphx copilot install")


def vscode_uninstall(project_dir: Path | None = None) -> None:
    """Remove graphx VS Code Copilot Chat skill and .github/copilot-instructions.md section."""
    skill_dst = Path.home() / ".copilot" / "skills" / "graphx" / "SKILL.md"
    if skill_dst.exists():
        skill_dst.unlink()
        print(f"  skill removed    ->  {skill_dst}")
    version_file = skill_dst.parent / ".graphx_version"
    if version_file.exists():
        version_file.unlink()
    for d in (skill_dst.parent, skill_dst.parent.parent, skill_dst.parent.parent.parent):
        try:
            d.rmdir()
        except OSError:
            break

    instructions = (project_dir or Path(".")) / ".github" / "copilot-instructions.md"
    if not instructions.exists():
        return
    content = instructions.read_text(encoding="utf-8")
    if _VSCODE_INSTRUCTIONS_MARKER not in content:
        return
    cleaned = re.sub(r"\n*## graphx\n.*?(?=\n## |\Z)", "", content, flags=re.DOTALL).rstrip()
    if cleaned:
        instructions.write_text(cleaned + "\n", encoding="utf-8")
        print(f"  graphx section removed from {instructions}")
    else:
        instructions.unlink()
        print(f"  {instructions}  ->  deleted (was empty after removal)")


_ANTIGRAVITY_RULES_PATH = Path(".agents") / "rules" / "graphx.md"
_ANTIGRAVITY_WORKFLOW_PATH = Path(".agents") / "workflows" / "graphx.md"

_ANTIGRAVITY_RULES = """\
## graphx

This project has a graphx knowledge graph at graphx-out/.

Rules:
- Before answering architecture or codebase questions, read graphx-out/GRAPH_REPORT.md for god nodes and community structure
- If graphx-out/wiki/index.md exists, navigate it instead of reading raw files
- If the graphx MCP server is active, utilize tools like `query_graph`, `get_node`, and `shortest_path` for precise architecture navigation instead of falling back to `grep`
- If the MCP server is not active, the CLI equivalents are `graphx query "<question>"`, `graphx path "<A>" "<B>"`, and `graphx explain "<concept>"` — prefer these over grep for cross-module questions
- After modifying code files in this session, run `graphx update .` to keep the graph current (AST-only, no API cost)
"""

_ANTIGRAVITY_WORKFLOW = """\
---
name: graphx
description: Turn any folder of files into a navigable knowledge graph
---

# Workflow: graphx

Follow the graphx skill installed at ~/.agents/skills/graphx/SKILL.md to run the full pipeline.

If no path argument is given, use `.` (current directory).
"""


_KIRO_STEERING = """\
---
inclusion: always
---

graphx: A knowledge graph of this project lives in `graphx-out/`. \
If `graphx-out/GRAPH_REPORT.md` exists, read it before answering architecture questions, \
tracing dependencies, or searching files — it contains god nodes, community structure, \
and surprising connections the graph found. Navigate by graph structure instead of grepping raw files.
"""

_KIRO_STEERING_MARKER = "graphx: A knowledge graph of this project"


def _kiro_install(project_dir: Path) -> None:
    """Write graphx skill + steering file for Kiro IDE/CLI."""
    project_dir = project_dir or Path(".")

    # Skill file → .kiro/skills/graphx/SKILL.md
    skill_src = Path(__file__).parent / "skill-kiro.md"
    skill_dst = project_dir / ".kiro" / "skills" / "graphx" / "SKILL.md"
    skill_dst.parent.mkdir(parents=True, exist_ok=True)
    skill_dst.write_text(skill_src.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"  {skill_dst.relative_to(project_dir)}  ->  /graphx skill")

    # Steering file → .kiro/steering/graphx.md (always-on)
    steering_dir = project_dir / ".kiro" / "steering"
    steering_dir.mkdir(parents=True, exist_ok=True)
    steering_dst = steering_dir / "graphx.md"
    if steering_dst.exists() and _KIRO_STEERING_MARKER in steering_dst.read_text(encoding="utf-8"):
        print(f"  .kiro/steering/graphx.md  ->  already configured")
    else:
        steering_dst.write_text(_KIRO_STEERING, encoding="utf-8")
        print(f"  .kiro/steering/graphx.md  ->  always-on steering written")

    print()
    print("Kiro will now read the knowledge graph before every conversation.")
    print("Use /graphx to build or update the graph.")


def _kiro_uninstall(project_dir: Path) -> None:
    """Remove graphx skill + steering file for Kiro."""
    project_dir = project_dir or Path(".")
    removed = []

    skill_dst = project_dir / ".kiro" / "skills" / "graphx" / "SKILL.md"
    if skill_dst.exists():
        skill_dst.unlink()
        removed.append(str(skill_dst.relative_to(project_dir)))
        # Remove parent dir if empty
        try:
            skill_dst.parent.rmdir()
        except OSError:
            pass

    steering_dst = project_dir / ".kiro" / "steering" / "graphx.md"
    if steering_dst.exists():
        steering_dst.unlink()
        removed.append(str(steering_dst.relative_to(project_dir)))

    print("Removed: " + (", ".join(removed) if removed else "nothing to remove"))


def _antigravity_install(project_dir: Path) -> None:
    """Install graphx for Google Antigravity: skill + .agents/rules + .agents/workflows."""
    # 1. Copy skill file to ~/.agents/skills/graphx/SKILL.md
    install(platform="antigravity")

    # 1.5. Inject YAML frontmatter for native Antigravity tool discovery
    skill_dst = Path.home() / _PLATFORM_CONFIG["antigravity"]["skill_dst"]
    if skill_dst.exists():
        content = skill_dst.read_text(encoding="utf-8")
        if not content.startswith("---\n"):
            frontmatter = "---\nname: graphx-manager\ndescription: Rebuild the code graph or perform manual CLI queries when MCP server is offline.\n---\n\n"
            skill_dst.write_text(frontmatter + content, encoding="utf-8")

    # 2. Write .agents/rules/graphx.md
    rules_path = project_dir / _ANTIGRAVITY_RULES_PATH
    rules_path.parent.mkdir(parents=True, exist_ok=True)
    if rules_path.exists():
        existing = rules_path.read_text(encoding="utf-8")
        if _ANTIGRAVITY_RULES.strip() != existing.strip():
            rules_path.write_text(_ANTIGRAVITY_RULES, encoding="utf-8")
            print(f"graphx rule updated at {rules_path.resolve()}")
        else:
            print(f"graphx rule already up to date at {rules_path.resolve()}")
    else:
        rules_path.write_text(_ANTIGRAVITY_RULES, encoding="utf-8")
        print(f"graphx rule written to {rules_path.resolve()}")

    # 3. Write .agents/workflows/graphx.md
    wf_path = project_dir / _ANTIGRAVITY_WORKFLOW_PATH
    wf_path.parent.mkdir(parents=True, exist_ok=True)
    if wf_path.exists():
        existing = wf_path.read_text(encoding="utf-8")
        if _ANTIGRAVITY_WORKFLOW.strip() != existing.strip():
            wf_path.write_text(_ANTIGRAVITY_WORKFLOW, encoding="utf-8")
            print(f"graphx workflow updated at {wf_path.resolve()}")
        else:
            print(f"graphx workflow already up to date at {wf_path.resolve()}")
    else:
        wf_path.write_text(_ANTIGRAVITY_WORKFLOW, encoding="utf-8")
        print(f"graphx workflow written to {wf_path.resolve()}")

    print()
    print("Antigravity will now check the knowledge graph before answering")
    print("codebase questions. Run /graphx first to build the graph.")
    print()
    print("To enable full MCP architecture navigation, add this to ~/.gemini/antigravity/mcp_config.json:")
    print('  "graphx": {')
    print('    "command": "uv",')
    print('    "args": ["run", "--with", "graphx", "--with", "mcp", "-m", "graphx.serve", "${workspace.path}/graphx-out/graph.json"]')
    print('  }')


def _antigravity_uninstall(project_dir: Path) -> None:
    """Remove graphx Antigravity rules, workflow, and skill files."""
    # Remove rules file
    rules_path = project_dir / _ANTIGRAVITY_RULES_PATH
    if rules_path.exists():
        rules_path.unlink()
        print(f"graphx rule removed from {rules_path.resolve()}")
    else:
        print("No graphx Antigravity rule found - nothing to do")

    # Remove workflow file
    wf_path = project_dir / _ANTIGRAVITY_WORKFLOW_PATH
    if wf_path.exists():
        wf_path.unlink()
        print(f"graphx workflow removed from {wf_path.resolve()}")

    # Remove skill file
    skill_dst = Path.home() / _PLATFORM_CONFIG["antigravity"]["skill_dst"]
    if skill_dst.exists():
        skill_dst.unlink()
        print(f"graphx skill removed from {skill_dst}")
    version_file = skill_dst.parent / ".graphx_version"
    if version_file.exists():
        version_file.unlink()
    for d in (skill_dst.parent, skill_dst.parent.parent, skill_dst.parent.parent.parent):
        try:
            d.rmdir()
        except OSError:
            break


_CURSOR_RULE_PATH = Path(".cursor") / "rules" / "graphx.mdc"
_CURSOR_RULE = """\
---
description: graphx knowledge graph context
alwaysApply: true
---

This project has a graphx knowledge graph at graphx-out/.

- Before answering architecture or codebase questions, read graphx-out/GRAPH_REPORT.md for god nodes and community structure
- If graphx-out/wiki/index.md exists, navigate it instead of reading raw files
- After modifying code files in this session, run `graphx update .` to keep the graph current (AST-only, no API cost)
"""


def _cursor_install(project_dir: Path) -> None:
    """Write .cursor/rules/graphx.mdc with alwaysApply: true."""
    rule_path = (project_dir or Path(".")) / _CURSOR_RULE_PATH
    rule_path.parent.mkdir(parents=True, exist_ok=True)
    if rule_path.exists():
        print(f"graphx rule already exists at {rule_path} (no change)")
        return
    rule_path.write_text(_CURSOR_RULE, encoding="utf-8")
    print(f"graphx rule written to {rule_path.resolve()}")
    print()
    print("Cursor will now always include the knowledge graph context.")
    print("Run /graphx . first to build the graph if you haven't already.")


def _cursor_uninstall(project_dir: Path) -> None:
    """Remove .cursor/rules/graphx.mdc."""
    rule_path = (project_dir or Path(".")) / _CURSOR_RULE_PATH
    if not rule_path.exists():
        print("No graphx Cursor rule found - nothing to do")
        return
    rule_path.unlink()
    print(f"graphx Cursor rule removed from {rule_path.resolve()}")


# --- Devin install / uninstall ---

def _devin_skill_dst() -> Path:
    r"""Return the Devin global skill directory.

    Devin global skills live at:
      Linux/macOS: ~/.config/devin/skills/
      Windows:     %APPDATA%/devin/skills/  (e.g. C:\Users\<you>\AppData\Roaming\devin\skills\)
    """
    home = Path.home()
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "devin" / "skills" / "graphx" / "SKILL.md"
        return home / "AppData" / "Roaming" / "devin" / "skills" / "graphx" / "SKILL.md"
    return home / ".config" / "devin" / "skills" / "graphx" / "SKILL.md"


def _devin_install() -> None:
    """Copy skill file to Devin's global skills directory."""
    skill_src = Path(__file__).parent / "skill-devin.md"
    if not skill_src.exists():
        # Fallback to generic skill.md if devin-specific doesn't exist
        skill_src = Path(__file__).parent / "skill.md"
    skill_dst = _devin_skill_dst()
    skill_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(skill_src, skill_dst)
    (skill_dst.parent / ".graphx_version").write_text(__version__, encoding="utf-8")
    print(f"  skill installed  ->  {skill_dst}")
    print()
    print("Devin for Terminal will now recognize /graphx in any session.")


def _devin_uninstall() -> None:
    """Remove graphx skill from Devin's global skills directory."""
    skill_dst = _devin_skill_dst()
    if skill_dst.exists():
        skill_dst.unlink()
        print(f"  skill removed    ->  {skill_dst}")
    version_file = skill_dst.parent / ".graphx_version"
    if version_file.exists():
        version_file.unlink()
    for d in (skill_dst.parent, skill_dst.parent.parent, skill_dst.parent.parent.parent):
        try:
            d.rmdir()
        except OSError:
            break


# OpenCode tool.execute.before plugin — fires before every tool call.
# Injects a graph reminder into bash command output when graph.json exists.
_OPENCODE_PLUGIN_JS = """\
// graphx OpenCode plugin
// Injects a knowledge graph reminder before bash tool calls when the graph exists.
import { existsSync } from "fs";
import { join } from "path";

export const GraphXPlugin = async ({ directory }) => {
  let reminded = false;

  return {
    "tool.execute.before": async (input, output) => {
      if (reminded) return;
      if (!existsSync(join(directory, "graphx-out", "graph.json"))) return;

      if (input.tool === "bash") {
        output.args.command =
          'echo "[graphx] Knowledge graph available. Read graphx-out/GRAPH_REPORT.md for god nodes and architecture context before searching files." && ' +
          output.args.command;
        reminded = true;
      }
    },
  };
};
"""

_OPENCODE_PLUGIN_PATH = Path(".opencode") / "plugins" / "graphx.js"
_OPENCODE_CONFIG_PATH = Path(".opencode") / "opencode.json"
_OPENCODE_COMMAND_PATH = Path.home() / ".config" / "opencode" / "commands" / "graphx.md"

_OPENCODE_COMMAND_MD = """\
---
description: Build or query the Ai-GraphX knowledge graph
---

Load and use the graphx skill. Execute `graphx $ARGUMENTS` in the terminal.
If no arguments are given, run `graphx watch .` to build or update the knowledge graph
for the current project. Then read `graphx-out/GRAPH_REPORT.md` for architecture context
and report key findings. Use `graphx-out/index.html` for the live activity dashboard
with real-time commit tracking.
"""


def _install_opencode_plugin(project_dir: Path) -> None:
    """Write graphx.js plugin, register it in opencode.json, and add /graphx custom command."""
    plugin_file = project_dir / _OPENCODE_PLUGIN_PATH
    plugin_file.parent.mkdir(parents=True, exist_ok=True)
    plugin_file.write_text(_OPENCODE_PLUGIN_JS, encoding="utf-8")
    print(f"  {_OPENCODE_PLUGIN_PATH}  ->  tool.execute.before hook written")

    config_file = project_dir / _OPENCODE_CONFIG_PATH
    if config_file.exists():
        try:
            config = json.loads(config_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            config = {}
    else:
        config = {}

    plugins = config.setdefault("plugin", [])
    entry = _OPENCODE_PLUGIN_PATH.as_posix()
    if entry not in plugins:
        plugins.append(entry)
        config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
        print(f"  {_OPENCODE_CONFIG_PATH}  ->  plugin registered")
    else:
        print(f"  {_OPENCODE_CONFIG_PATH}  ->  plugin already registered (no change)")

    # Register global /graphx custom command
    _OPENCODE_COMMAND_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OPENCODE_COMMAND_PATH.write_text(_OPENCODE_COMMAND_MD, encoding="utf-8")
    cmd_path = Path("~/.config/opencode/commands/graphx.md").expanduser()
    print(f"  {cmd_path}  ->  /graphx custom command registered")


def _uninstall_opencode_plugin(project_dir: Path) -> None:
    """Remove graphx.js plugin, deregister from opencode.json, and remove /graphx command."""
    plugin_file = project_dir / _OPENCODE_PLUGIN_PATH
    if plugin_file.exists():
        plugin_file.unlink()
        print(f"  {_OPENCODE_PLUGIN_PATH}  ->  removed")

    config_file = project_dir / _OPENCODE_CONFIG_PATH
    if not config_file.exists():
        return
    try:
        config = json.loads(config_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    plugins = config.get("plugin", [])
    entry = _OPENCODE_PLUGIN_PATH.as_posix()
    if entry in plugins:
        plugins.remove(entry)
        if not plugins:
            config.pop("plugin")
        config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
        print(f"  {_OPENCODE_CONFIG_PATH}  ->  plugin deregistered")

    # Remove global /graphx custom command
    if _OPENCODE_COMMAND_PATH.exists():
        _OPENCODE_COMMAND_PATH.unlink()
        cmd_path = Path("~/.config/opencode/commands/graphx.md").expanduser()
        print(f"  {cmd_path}  ->  /graphx custom command removed")


_CODEX_HOOK = {
    "hooks": {
        "PreToolUse": [
            {
                "matcher": "Bash",
                "hooks": [
                    {
                        "type": "command",
                        # Use the graphx CLI itself so the hook is shell-agnostic:
                        # no [ -f ] bash syntax, no python3 vs python Conda issue,
                        # no JSON escaping inside PowerShell strings. Works on
                        # Windows (PowerShell/cmd.exe), macOS, and Linux.
                        "command": "graphx hook-check",
                    }
                ],
            }
        ]
    }
}


def _resolve_graphx_exe() -> str:
    """Return the absolute path to the graphx executable.

    Falls back to bare 'graphx' if resolution fails. Using an absolute path
    ensures the hook works in environments where the venv Scripts/ directory is
    not on PATH (e.g. VS Code Codex extension on Windows).
    """
    import shutil
    found = shutil.which("graphx")
    if found:
        return found
    # Derive from sys.executable: same Scripts/ (Windows) or bin/ (Unix) dir
    scripts_dir = Path(sys.executable).parent
    for name in ("graphx.exe", "graphx"):
        candidate = scripts_dir / name
        if candidate.exists():
            return str(candidate)
    return "graphx"


def _install_codex_hook(project_dir: Path) -> None:
    """Add graphx PreToolUse hook to .codex/hooks.json."""
    hooks_path = project_dir / ".codex" / "hooks.json"
    hooks_path.parent.mkdir(parents=True, exist_ok=True)

    if hooks_path.exists():
        try:
            existing = json.loads(hooks_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    else:
        existing = {}

    graphx_exe = _resolve_graphx_exe()
    hook_entry = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [{"type": "command", "command": f"{graphx_exe} hook-check"}],
                }
            ]
        }
    }

    pre_tool = existing.setdefault("hooks", {}).setdefault("PreToolUse", [])
    existing["hooks"]["PreToolUse"] = [h for h in pre_tool if "graphx" not in str(h)]
    existing["hooks"]["PreToolUse"].extend(hook_entry["hooks"]["PreToolUse"])
    hooks_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    print(f"  .codex/hooks.json  ->  PreToolUse hook registered ({graphx_exe} hook-check)")


def _uninstall_codex_hook(project_dir: Path) -> None:
    """Remove graphx PreToolUse hook from .codex/hooks.json."""
    hooks_path = project_dir / ".codex" / "hooks.json"
    if not hooks_path.exists():
        return
    try:
        existing = json.loads(hooks_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    pre_tool = existing.get("hooks", {}).get("PreToolUse", [])
    filtered = [h for h in pre_tool if "graphx" not in str(h)]
    existing["hooks"]["PreToolUse"] = filtered
    hooks_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    print(f"  .codex/hooks.json  ->  PreToolUse hook removed")


def _agents_install(project_dir: Path, platform: str) -> None:
    """Write the graphx section to the local AGENTS.md (Codex/OpenCode/OpenClaw)."""
    target = (project_dir or Path(".")) / "AGENTS.md"

    if target.exists():
        content = target.read_text(encoding="utf-8")
        if _AGENTS_MD_MARKER in content:
            print(f"graphx already configured in AGENTS.md")
        else:
            target.write_text(content.rstrip() + "\n\n" + _AGENTS_MD_SECTION, encoding="utf-8")
            print(f"graphx section written to {target.resolve()}")
    else:
        target.write_text(_AGENTS_MD_SECTION, encoding="utf-8")
        print(f"graphx section written to {target.resolve()}")

    if platform == "codex":
        _install_codex_hook(project_dir or Path("."))
    elif platform == "opencode":
        _install_opencode_plugin(project_dir or Path("."))

    print()
    print(f"{platform.capitalize()} will now check the knowledge graph before answering")
    print("codebase questions and rebuild it after code changes.")
    if platform not in ("codex", "opencode"):
        print()
        print("Note: unlike Claude Code, there is no PreToolUse hook equivalent for")
        print(f"{platform.capitalize()} — the AGENTS.md rules are the always-on mechanism.")


def _agents_uninstall(project_dir: Path, platform: str = "") -> None:
    """Remove the graphx section from the local AGENTS.md."""
    target = (project_dir or Path(".")) / "AGENTS.md"

    if not target.exists():
        print("No AGENTS.md found in current directory - nothing to do")
        return

    content = target.read_text(encoding="utf-8")
    if _AGENTS_MD_MARKER not in content:
        print("graphx section not found in AGENTS.md - nothing to do")
        return

    cleaned = re.sub(
        r"\n*## graphx\n.*?(?=\n## |\Z)",
        "",
        content,
        flags=re.DOTALL,
    ).rstrip()
    if cleaned:
        target.write_text(cleaned + "\n", encoding="utf-8")
        print(f"graphx section removed from {target.resolve()}")
    else:
        target.unlink()
        print(f"AGENTS.md was empty after removal - deleted {target.resolve()}")

    if platform == "opencode":
        _uninstall_opencode_plugin(project_dir or Path("."))


def claude_install(project_dir: Path | None = None) -> None:
    """Write the graphx section to the local CLAUDE.md."""
    target = (project_dir or Path(".")) / "CLAUDE.md"

    if target.exists():
        content = target.read_text(encoding="utf-8")
        if _CLAUDE_MD_MARKER in content:
            print("graphx already configured in CLAUDE.md")
            return
        new_content = content.rstrip() + "\n\n" + _CLAUDE_MD_SECTION
    else:
        new_content = _CLAUDE_MD_SECTION

    target.write_text(new_content, encoding="utf-8")
    print(f"graphx section written to {target.resolve()}")

    # Also write Claude Code PreToolUse hook to .claude/settings.json
    _install_claude_hook(project_dir or Path("."))

    print()
    print("Claude Code will now check the knowledge graph before answering")
    print("codebase questions and rebuild it after code changes.")


def _install_claude_hook(project_dir: Path) -> None:
    """Add graphx PreToolUse hook to .claude/settings.json."""
    settings_path = project_dir / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            settings = {}
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool = hooks.setdefault("PreToolUse", [])

    hooks["PreToolUse"] = [h for h in pre_tool if not (h.get("matcher") in ("Glob|Grep", "Bash") and "graphx" in str(h))]
    hooks["PreToolUse"].append(_SETTINGS_HOOK)
    settings_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    print(f"  .claude/settings.json  ->  PreToolUse hook registered")


def _uninstall_claude_hook(project_dir: Path) -> None:
    """Remove graphx PreToolUse hook from .claude/settings.json."""
    settings_path = project_dir / ".claude" / "settings.json"
    if not settings_path.exists():
        return
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    pre_tool = settings.get("hooks", {}).get("PreToolUse", [])
    filtered = [h for h in pre_tool if not (h.get("matcher") in ("Glob|Grep", "Bash") and "graphx" in str(h))]
    if len(filtered) == len(pre_tool):
        return
    settings["hooks"]["PreToolUse"] = filtered
    settings_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    print(f"  .claude/settings.json  ->  PreToolUse hook removed")


def claude_uninstall(project_dir: Path | None = None) -> None:
    """Remove the graphx section from the local CLAUDE.md."""
    target = (project_dir or Path(".")) / "CLAUDE.md"

    if not target.exists():
        print("No CLAUDE.md found in current directory - nothing to do")
        return

    content = target.read_text(encoding="utf-8")
    if _CLAUDE_MD_MARKER not in content:
        print("graphx section not found in CLAUDE.md - nothing to do")
        return

    # Remove the ## graphx section: from the marker to the next ## heading or EOF
    cleaned = re.sub(
        r"\n*## graphx\n.*?(?=\n## |\Z)",
        "",
        content,
        flags=re.DOTALL,
    ).rstrip()
    if cleaned:
        target.write_text(cleaned + "\n", encoding="utf-8")
        print(f"graphx section removed from {target.resolve()}")
    else:
        target.unlink()
        print(f"CLAUDE.md was empty after removal - deleted {target.resolve()}")

    _uninstall_claude_hook(project_dir or Path("."))


def _clone_repo(url: str, branch: str | None = None, out_dir: Path | None = None) -> Path:
    """Clone a GitHub repo to a local cache dir and return the path.

    Clones into ~/.graphx/repos/<owner>/<repo> by default so repeated
    runs on the same URL reuse the existing clone (git pull instead of clone).
    """
    import subprocess as _sp
    import re as _re

    # Normalise URL — strip trailing .git if present
    url = url.rstrip("/")
    if not url.endswith(".git"):
        git_url = url + ".git"
    else:
        git_url = url
        url = url[:-4]

    # Extract owner/repo from URL
    m = _re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", url)
    if not m:
        print(f"error: not a recognised GitHub URL: {url}", file=sys.stderr)
        sys.exit(1)
    owner, repo = m.group(1), m.group(2)

    if out_dir:
        dest = out_dir
    else:
        dest = Path.home() / ".graphx" / "repos" / owner / repo

    if branch and branch.startswith("-"):
        print(f"error: invalid branch name: {branch!r}", file=sys.stderr)
        sys.exit(1)

    if dest.exists():
        print(f"Repo already cloned at {dest} — pulling latest...", flush=True)
        cmd = ["git", "-C", str(dest), "pull"]
        if branch:
            cmd += ["origin", "--", branch]
        result = _sp.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"warning: git pull failed:\n{result.stderr}", file=sys.stderr)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"Cloning {url} → {dest} ...", flush=True)
        cmd = ["git", "clone", "--depth", "1"]
        if branch:
            cmd += ["--branch", branch]
        cmd += ["--", git_url, str(dest)]
        result = _sp.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"error: git clone failed:\n{result.stderr}", file=sys.stderr)
            sys.exit(1)

    print(f"Ready at: {dest}", flush=True)
    return dest


def self_update() -> None:
    """Update graphx package to the latest version from GitHub."""
    repo_url = "https://github.com/BlackWh1te/GraphX.git"
    cache_dir = Path.home() / ".graphx" / "self-update"
    cache_dir.mkdir(parents=True, exist_ok=True)
    repo_dir = cache_dir / "GraphX"

    # Show current version
    try:
        current_version = __version__
        print(f"Current version: {current_version}")
    except:
        current_version = "unknown"
        print(f"Current version: {current_version}")

    print()
    print("Updating graphx to latest version...")
    print(f"Fetching from {repo_url}")
    print()

    # Clone or pull the repo
    if repo_dir.exists():
        print("Updating existing clone...")
        try:
            subprocess.run(
                ["git", "fetch", "origin"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                check=True
            )
            subprocess.run(
                ["git", "reset", "--hard", "origin/main"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                check=True
            )
            print("Repository updated.")
        except subprocess.CalledProcessError as e:
            print(f"Git update failed: {e}", file=sys.stderr)
            print("Trying fresh clone...", file=sys.stderr)
            shutil.rmtree(repo_dir)
            _clone_repo(repo_url, None, repo_dir)
    else:
        print("Cloning repository...")
        _clone_repo(repo_url, None, repo_dir)

    print()
    print("Installing updated package...")

    # Detect Python and install
    python = sys.executable

    try:
        # Install in editable mode for development
        result = subprocess.run(
            [python, "-m", "pip", "install", "-e", str(repo_dir), "--upgrade"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✓ graphx updated successfully!")
        print()

        # Show new version
        try:
            from importlib.metadata import version as _pkg_version_new
            new_version = _pkg_version_new("graphx")
            print(f"New version: {new_version}")
            if current_version != "unknown" and current_version != new_version:
                print(f"Updated from {current_version} → {new_version}")
        except:
            pass

        print()
        print("Run 'graphx --version' to verify the new version.")
    except subprocess.CalledProcessError as e:
        print(f"Installation failed: {e}", file=sys.stderr)
        if e.stderr:
            print(f"stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def _check_any_skills_installed() -> bool:
    """Check if any graphx skills are installed in any platform."""
    for cfg in _PLATFORM_CONFIG.values():
        skill_dst = Path.home() / cfg["skill_dst"]
        if skill_dst.exists():
            return True
    # Also check Devin
    devin_dst = _devin_skill_dst()
    if devin_dst.exists():
        return True
    return False


def main() -> None:
    # Parse global flags before command
    args = sys.argv[1:]
    skip_auto_install = "--no-auto-install" in args
    # Remove the flag from args so command parsing works
    if skip_auto_install:
        sys.argv = [sys.argv[0]] + [arg for arg in args if arg != "--no-auto-install"]

    # Auto-install skills on first run if none are installed
    # Skip if: install/uninstall commands, --no-auto-install flag, or GRAPHX_NO_AUTO_INSTALL env var
    should_auto_install = (
        not skip_auto_install
        and not os.environ.get("GRAPHX_NO_AUTO_INSTALL")
        and not any(arg in ("install", "uninstall") for arg in sys.argv)
    )

    if should_auto_install and not _check_any_skills_installed():
        print("No graphx skills installed.")
        print()
        detected = _detect_installed_platforms()
        if detected:
            print(f"Detected AI assistants: {', '.join(detected)}")
            print()
            response = input("Auto-install graphx skills for these assistants? [Y/n] ").strip().lower()
            if response in ("", "y", "yes"):
                print()
                print("Installing skills...")
                print()
                success = 0
                for plat in detected:
                    print(f"Installing to {plat}...")
                    if _install_single(plat):
                        success += 1
                    print()
                _refresh_all_version_stamps()
                print(f"Done. Installed to {success}/{len(detected)} platform(s).")
                print()
                print("You can now use /graphx in your AI assistant.")
                print()
        else:
            default_platform = "windows" if platform.system() == "Windows" else "claude"
            print(f"No AI assistant configurations found.")
            print(f"Install default ({default_platform})? [Y/n] ", end="")
            response = input().strip().lower()
            if response in ("", "y", "yes"):
                print()
                print(f"Installing to {default_platform}...")
                install(platform=default_platform)
                print()
                print("You can now use /graphx in your AI assistant.")
                print()
        print("To skip this prompt in the future, use: graphx --no-auto-install <command>")
        print("Or set env var: export GRAPHX_NO_AUTO_INSTALL=1")
        print()

    # Check all known skill install locations for a stale version stamp.
    # Skip during install/uninstall (hook writes trigger a fresh check anyway).
    # Deduplicate paths so platforms sharing the same install dir don't warn twice.
    if not any(arg in ("install", "uninstall") for arg in sys.argv):
        for skill_dst in {Path.home() / cfg["skill_dst"] for cfg in _PLATFORM_CONFIG.values()}:
            _check_skill_version(skill_dst)

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: graphx <command>")
        print()
        print("Note: On first run, graphx will offer to auto-install skills for detected AI assistants.")
        print("      Use --no-auto-install to skip, or set GRAPHX_NO_AUTO_INSTALL=1")
        print()
        print("Commands:")
        print("  --version               show installed graphx version")
        print("  install [--platform P]  auto-detect AI assistants and install to all (or one)")
        print("                          omit --platform to scan home dir and install everywhere found")
        print("                          --platform P installs to a specific assistant only")
        print("  path \"A\" \"B\"            shortest path between two nodes in graph.json")
        print("    --graph <path>          path to graph.json (default graphx-out/graph.json)")
        print("  explain \"X\"             plain-language explanation of a node and its neighbors")
        print("    --graph <path>          path to graph.json (default graphx-out/graph.json)")
        print("  clone <github-url>      clone a GitHub repo locally and print its path for /graphx")
        print("  merge-graphs <g1> <g2>  merge two or more graph.json files into one cross-repo graph")
        print("    --out <path>            output path (default: graphx-out/merged-graph.json)")
        print("    --branch <branch>       checkout a specific branch (default: repo default)")
        print("    --out <dir>             clone to a custom directory (default: ~/.graphx/repos/<owner>/<repo>)")
        print("  add <url>               fetch a URL and save it to ./raw, then update the graph")
        print("    --author \"Name\"         tag the author of the content")
        print("    --contributor \"Name\"    tag who added it to the corpus")
        print("    --dir <path>            target directory (default: ./raw)")
        print("  watch <path>            watch a folder and rebuild the graph on code changes")
        print("  update                  update graphx package to latest version from GitHub")
        print("  update <path>           re-extract code files and update the graph (no LLM needed)")
        print("    --pull                  run 'git pull' before updating to fetch latest changes")
        print("    --force                 overwrite graph.json even if the rebuild has fewer nodes")
        print("                            (also: GRAPHX_FORCE=1 env var; use after refactors that delete code)")
        print("  cluster-only <path>     rerun clustering on an existing graph.json and regenerate report")
        print("    --no-viz                skip graph.html generation (useful for >5000 node graphs / CI)")
        print("  query \"<question>\"       BFS traversal of graph.json for a question")
        print("    --dfs                   use depth-first instead of breadth-first")
        print("    --context C             explicit edge-context filter (repeatable)")
        print("    --budget N              cap output at N tokens (default 2000)")
        print("    --graph <path>          path to graph.json (default graphx-out/graph.json)")
        print("  save-result             save a Q&A result to graphx-out/memory/ for graph feedback loop")
        print("    --question Q            the question asked")
        print("    --answer A              the answer to save")
        print("    --type T                query type: query|path_query|explain (default: query)")
        print("    --nodes N1 N2 ...       source node labels cited in the answer")
        print("    --memory-dir DIR        memory directory (default: graphx-out/memory)")
        print("  check-update <path>     check needs_update flag and notify if semantic re-extraction is pending (cron-safe)")
        print("  log <title>             log a work session to changelog.json")
        print("    --description TEXT     description of what was done")
        print("    --files PATH,PATH      comma-separated list of changed files")
        print("    --tags TAG,TAG         comma-separated tags (e.g., feature,auth)")
        print("  tree                    emit a D3 v7 collapsible-tree HTML for graph.json")
        print("    --graph PATH            path to graph.json (default graphx-out/graph.json)")
        print("    --output HTML           output path (default graphx-out/GRAPH_TREE.html)")
        print("    --root PATH             filesystem root for the hierarchy")
        print("    --max-children N        cap children per node (default 200)")
        print("    --top-k-edges N         per-symbol outbound edges in inspector (default 12)")
        print("    --label NAME            project label in header")
        print("  index                   generate index.html dashboard for all outputs")
        print("    --graph PATH            path to graph.json (default graphx-out/graph.json)")
        print("    --output DIR            output directory (default: same as graph.json)")
        print("    --name NAME             project name for the dashboard title")
        print("  status [path]            show project status dashboard")
        print("    Shows: Graph health (nodes, edges, communities, last build),")
        print("           AI vs User vs External changes, external files, branch status,")
        print("           merge commits, large files, staged changes, hot files, velocity")
        print("  capture-commit          capture current git commit metadata (called by hook)")
        print("  benchmark [graph.json]  measure token reduction vs naive full-corpus approach")
        print("  hook install            install post-commit/post-checkout git hooks (all platforms)")
        print("  hook uninstall          remove git hooks")
        print("  hook status             check if git hooks are installed")
        print("  gemini install          write GEMINI.md section + BeforeTool hook (Gemini CLI)")
        print("  gemini uninstall        remove GEMINI.md section + BeforeTool hook")
        print("  cursor install          write .cursor/rules/graphx.mdc (Cursor)")
        print("  cursor uninstall        remove .cursor/rules/graphx.mdc")
        print("  claude install          write graphx section to CLAUDE.md + PreToolUse hook (Claude Code)")
        print("  claude uninstall        remove graphx section from CLAUDE.md + PreToolUse hook")
        print("  codex install           write graphx section to AGENTS.md (Codex)")
        print("  codex uninstall         remove graphx section from AGENTS.md")
        print("  opencode install        write graphx section to AGENTS.md + tool.execute.before plugin (OpenCode)")
        print("  opencode uninstall      remove graphx section from AGENTS.md + plugin")
        print("  aider install           write graphx section to AGENTS.md (Aider)")
        print("  aider uninstall         remove graphx section from AGENTS.md")
        print("  copilot install         copy graphx skill to ~/.copilot/skills (GitHub Copilot CLI)")
        print("  copilot uninstall       remove graphx skill from ~/.copilot/skills")
        print("  vscode install          configure VS Code Copilot Chat (skill + .github/copilot-instructions.md)")
        print("  vscode uninstall        remove VS Code Copilot Chat configuration")
        print("  claw install            write graphx section to AGENTS.md (OpenClaw)")
        print("  claw uninstall          remove graphx section from AGENTS.md")
        print("  droid install           write graphx section to AGENTS.md (Factory Droid)")
        print("  droid uninstall        remove graphx section from AGENTS.md")
        print("  trae install            write graphx section to AGENTS.md (Trae)")
        print("  trae uninstall         remove graphx section from AGENTS.md")
        print("  trae-cn install         write graphx section to AGENTS.md (Trae CN)")
        print("  trae-cn uninstall      remove graphx section from AGENTS.md")
        print("  antigravity install     write .agents/rules + .agents/workflows + skill (Google Antigravity)")
        print("  antigravity uninstall   remove .agents/rules, .agents/workflows, and skill")
        print("  hermes install          write skill to ~/.hermes/skills/graphx/ (Hermes)")
        print("  hermes uninstall        remove skill from ~/.hermes/skills/graphx/")
        print("  kiro install            write skill to .kiro/skills/graphx/ + steering file (Kiro IDE/CLI)")
        print("  kiro uninstall          remove skill + steering file")
        print("  pi install              write skill to ~/.pi/agent/skills/graphx/ (Pi coding agent)")
        print("  pi uninstall            remove skill from ~/.pi/agent/skills/graphx/")
        print()
        return

    cmd = sys.argv[1]
    if cmd == "--version":
        print(f"graphx {__version__}")
        sys.exit(0)
    elif cmd == "install":
        # Parse args
        chosen_platform: str | None = None
        args = sys.argv[2:]
        i = 0
        while i < len(args):
            if args[i].startswith("--platform="):
                chosen_platform = args[i].split("=", 1)[1]
                i += 1
            elif args[i] == "--platform" and i + 1 < len(args):
                chosen_platform = args[i + 1]
                i += 2
            else:
                i += 1

        if chosen_platform:
            # Explicit platform: single install (legacy behavior)
            install(platform=chosen_platform)
        else:
            # Auto-detect: scan home dir for all configured AI assistants
            detected = _detect_installed_platforms()
            if detected:
                print(f"Detected {len(detected)} AI assistant(s): {', '.join(detected)}")
                print()
                success = 0
                for plat in detected:
                    print(f"Installing to {plat}...")
                    if _install_single(plat):
                        success += 1
                    print()
                _refresh_all_version_stamps()
                print(f"Done. Installed to {success}/{len(detected)} platform(s).")
                print("Type /graphx . in any of your assistants.")
            else:
                # Nothing detected — fall back to default single install
                default_platform = "windows" if platform.system() == "Windows" else "claude"
                print("No AI assistant configurations found in home directory.")
                print(f"Installing default: {default_platform}")
                print()
                install(platform=default_platform)
    elif cmd == "claude":
        subcmd = sys.argv[2] if len(sys.argv) > 2 else ""
        if subcmd == "install":
            claude_install()
        elif subcmd == "uninstall":
            claude_uninstall()
        else:
            print("Usage: graphx claude [install|uninstall]", file=sys.stderr)
            sys.exit(1)
    elif cmd == "gemini":
        subcmd = sys.argv[2] if len(sys.argv) > 2 else ""
        if subcmd == "install":
            gemini_install()
        elif subcmd == "uninstall":
            gemini_uninstall()
        else:
            print("Usage: graphx gemini [install|uninstall]", file=sys.stderr)
            sys.exit(1)
    elif cmd == "cursor":
        subcmd = sys.argv[2] if len(sys.argv) > 2 else ""
        if subcmd == "install":
            _cursor_install(Path("."))
        elif subcmd == "uninstall":
            _cursor_uninstall(Path("."))
        else:
            print("Usage: graphx cursor [install|uninstall]", file=sys.stderr)
            sys.exit(1)
    elif cmd == "vscode":
        subcmd = sys.argv[2] if len(sys.argv) > 2 else ""
        if subcmd == "install":
            vscode_install()
        elif subcmd == "uninstall":
            vscode_uninstall()
        else:
            print("Usage: graphx vscode [install|uninstall]", file=sys.stderr)
            sys.exit(1)
    elif cmd == "copilot":
        subcmd = sys.argv[2] if len(sys.argv) > 2 else ""
        if subcmd == "install":
            install(platform="copilot")
        elif subcmd == "uninstall":
            skill_dst = Path.home() / _PLATFORM_CONFIG["copilot"]["skill_dst"]
            removed = []
            if skill_dst.exists():
                skill_dst.unlink()
                removed.append(f"skill removed: {skill_dst}")
            version_file = skill_dst.parent / ".graphx_version"
            if version_file.exists():
                version_file.unlink()
            for d in (skill_dst.parent, skill_dst.parent.parent, skill_dst.parent.parent.parent):
                try:
                    d.rmdir()
                except OSError:
                    break
            print("; ".join(removed) if removed else "nothing to remove")
        else:
            print("Usage: graphx copilot [install|uninstall]", file=sys.stderr)
            sys.exit(1)
    elif cmd == "kiro":
        subcmd = sys.argv[2] if len(sys.argv) > 2 else ""
        if subcmd == "install":
            _kiro_install(Path("."))
        elif subcmd == "uninstall":
            _kiro_uninstall(Path("."))
        else:
            print("Usage: graphx kiro [install|uninstall]", file=sys.stderr)
            sys.exit(1)
    elif cmd == "pi":
        subcmd = sys.argv[2] if len(sys.argv) > 2 else ""
        if subcmd == "install":
            install("pi")
        elif subcmd == "uninstall":
            skill_dst = Path.home() / ".pi" / "agent" / "skills" / "graphx" / "SKILL.md"
            if skill_dst.exists():
                skill_dst.unlink()
                print(f"  skill removed    ->  {skill_dst}")
            version_file = skill_dst.parent / ".graphx_version"
            if version_file.exists():
                version_file.unlink()
            for d in (skill_dst.parent, skill_dst.parent.parent, skill_dst.parent.parent.parent):
                try:
                    d.rmdir()
                except OSError:
                    break
        else:
            print("Usage: graphx pi [install|uninstall]", file=sys.stderr)
            sys.exit(1)
    elif cmd in ("aider", "codex", "opencode", "claw", "droid", "trae", "trae-cn", "hermes"):
        subcmd = sys.argv[2] if len(sys.argv) > 2 else ""
        if subcmd == "install":
            _agents_install(Path("."), cmd)
        elif subcmd == "uninstall":
            _agents_uninstall(Path("."), platform=cmd)
            if cmd == "codex":
                _uninstall_codex_hook(Path("."))
        else:
            print(f"Usage: graphx {cmd} [install|uninstall]", file=sys.stderr)
            sys.exit(1)
    elif cmd == "antigravity":
        subcmd = sys.argv[2] if len(sys.argv) > 2 else ""
        if subcmd == "install":
            _antigravity_install(Path("."))
        elif subcmd == "uninstall":
            _antigravity_uninstall(Path("."))
        else:
            print("Usage: graphx antigravity [install|uninstall]", file=sys.stderr)
            sys.exit(1)
    elif cmd == "hook":
        from graphx.hooks import install as hook_install, uninstall as hook_uninstall, status as hook_status
        subcmd = sys.argv[2] if len(sys.argv) > 2 else ""
        if subcmd == "install":
            print(hook_install(Path(".")))
        elif subcmd == "uninstall":
            print(hook_uninstall(Path(".")))
        elif subcmd == "status":
            print(hook_status(Path(".")))
        else:
            print("Usage: graphx hook [install|uninstall|status]", file=sys.stderr)
            sys.exit(1)
    elif cmd == "query":
        if len(sys.argv) < 3:
            print("Usage: graphx query \"<question>\" [--dfs] [--context C] [--budget N] [--graph path]", file=sys.stderr)
            sys.exit(1)
        from graphx.serve import _query_graph_text
        from graphx.security import sanitize_label
        from networkx.readwrite import json_graph
        question = sys.argv[2]
        use_dfs = "--dfs" in sys.argv
        budget = 2000
        graph_path = "graphx-out/graph.json"
        context_filters: list[str] = []
        args = sys.argv[3:]
        i = 0
        while i < len(args):
            if args[i] == "--budget" and i + 1 < len(args):
                try:
                    budget = int(args[i + 1])
                except ValueError:
                    print(f"error: --budget must be an integer", file=sys.stderr)
                    sys.exit(1)
                i += 2
            elif args[i].startswith("--budget="):
                try:
                    budget = int(args[i].split("=", 1)[1])
                except ValueError:
                    print(f"error: --budget must be an integer", file=sys.stderr)
                    sys.exit(1)
                i += 1
            elif args[i] == "--context" and i + 1 < len(args):
                context_filters.append(args[i + 1])
                i += 2
            elif args[i].startswith("--context="):
                context_filters.append(args[i].split("=", 1)[1])
                i += 1
            elif args[i] == "--graph" and i + 1 < len(args):
                graph_path = args[i + 1]; i += 2
            else:
                i += 1
        gp = Path(graph_path).resolve()
        if not gp.exists():
            print(f"error: graph file not found: {gp}", file=sys.stderr)
            sys.exit(1)
        if not gp.suffix == ".json":
            print(f"error: graph file must be a .json file", file=sys.stderr)
            sys.exit(1)
        try:
            import json as _json
            import networkx as _nx
            _raw = _json.loads(gp.read_text(encoding="utf-8"))
            try:
                G = json_graph.node_link_graph(_raw, edges="links")
            except TypeError:
                G = json_graph.node_link_graph(_raw)
        except Exception as exc:
            print(f"error: could not load graph: {exc}", file=sys.stderr)
            sys.exit(1)
        print(
            _query_graph_text(
                G,
                question,
                mode="dfs" if use_dfs else "bfs",
                depth=2,
                token_budget=budget,
                context_filters=context_filters,
            )
        )
    elif cmd == "save-result":
        # graphx save-result --question Q --answer A --type T [--nodes N1 N2 ...]
        import argparse as _ap
        p = _ap.ArgumentParser(prog="graphx save-result")
        p.add_argument("--question", required=True)
        p.add_argument("--answer", required=True)
        p.add_argument("--type", dest="query_type", default="query")
        p.add_argument("--nodes", nargs="*", default=[])
        p.add_argument("--memory-dir", default="graphx-out/memory")
        opts = p.parse_args(sys.argv[2:])
        from graphx.ingest import save_query_result as _sqr
        out = _sqr(
            question=opts.question,
            answer=opts.answer,
            memory_dir=Path(opts.memory_dir),
            query_type=opts.query_type,
            source_nodes=opts.nodes or None,
        )
        print(f"Saved to {out}")
    elif cmd == "path":
        if len(sys.argv) < 4:
            print("Usage: graphx path \"<source>\" \"<target>\" [--graph path]", file=sys.stderr)
            sys.exit(1)
        from graphx.serve import _score_nodes
        from networkx.readwrite import json_graph
        import networkx as _nx
        source_label = sys.argv[2]
        target_label = sys.argv[3]
        graph_path = "graphx-out/graph.json"
        args = sys.argv[4:]
        for i, a in enumerate(args):
            if a == "--graph" and i + 1 < len(args):
                graph_path = args[i + 1]
        gp = Path(graph_path).resolve()
        if not gp.exists():
            print(f"error: graph file not found: {gp}", file=sys.stderr)
            sys.exit(1)
        _raw = json.loads(gp.read_text(encoding="utf-8"))
        try:
            G = json_graph.node_link_graph(_raw, edges="links")
        except TypeError:
            G = json_graph.node_link_graph(_raw)
        src_scored = _score_nodes(G, [t.lower() for t in source_label.split()])
        tgt_scored = _score_nodes(G, [t.lower() for t in target_label.split()])
        if not src_scored:
            print(f"No node matching '{source_label}' found.", file=sys.stderr)
            sys.exit(1)
        if not tgt_scored:
            print(f"No node matching '{target_label}' found.", file=sys.stderr)
            sys.exit(1)
        src_nid, tgt_nid = src_scored[0][1], tgt_scored[0][1]
        try:
            path_nodes = _nx.shortest_path(G, src_nid, tgt_nid)
        except (_nx.NetworkXNoPath, _nx.NodeNotFound):
            print(f"No path found between '{source_label}' and '{target_label}'.")
            sys.exit(0)
        hops = len(path_nodes) - 1
        segments = []
        for i in range(len(path_nodes) - 1):
            u, v = path_nodes[i], path_nodes[i + 1]
            edata = G.edges[u, v]
            rel = edata.get("relation", "")
            conf = edata.get("confidence", "")
            conf_str = f" [{conf}]" if conf else ""
            if i == 0:
                segments.append(G.nodes[u].get("label", u))
            segments.append(f"--{rel}{conf_str}--> {G.nodes[v].get('label', v)}")
        print(f"Shortest path ({hops} hops):\n  " + " ".join(segments))

    elif cmd == "explain":
        if len(sys.argv) < 3:
            print("Usage: graphx explain \"<node>\" [--graph path]", file=sys.stderr)
            sys.exit(1)
        from graphx.serve import _find_node
        from networkx.readwrite import json_graph
        label = sys.argv[2]
        graph_path = "graphx-out/graph.json"
        args = sys.argv[3:]
        for i, a in enumerate(args):
            if a == "--graph" and i + 1 < len(args):
                graph_path = args[i + 1]
        gp = Path(graph_path).resolve()
        if not gp.exists():
            print(f"error: graph file not found: {gp}", file=sys.stderr)
            sys.exit(1)
        _raw = json.loads(gp.read_text(encoding="utf-8"))
        try:
            G = json_graph.node_link_graph(_raw, edges="links")
        except TypeError:
            G = json_graph.node_link_graph(_raw)
        matches = _find_node(G, label)
        if not matches:
            print(f"No node matching '{label}' found.")
            sys.exit(0)
        nid = matches[0]
        d = G.nodes[nid]
        print(f"Node: {d.get('label', nid)}")
        print(f"  ID:        {nid}")
        print(f"  Source:    {d.get('source_file', '')} {d.get('source_location', '')}".rstrip())
        print(f"  Type:      {d.get('file_type', '')}")
        print(f"  Community: {d.get('community', '')}")
        print(f"  Degree:    {G.degree(nid)}")
        neighbors = list(G.neighbors(nid))
        if neighbors:
            print(f"\nConnections ({len(neighbors)}):")
            for nb in sorted(neighbors, key=lambda n: G.degree(n), reverse=True)[:20]:
                edata = G.edges[nid, nb]
                rel = edata.get("relation", "")
                conf = edata.get("confidence", "")
                print(f"  --> {G.nodes[nb].get('label', nb)} [{rel}] [{conf}]")
            if len(neighbors) > 20:
                print(f"  ... and {len(neighbors) - 20} more")

    elif cmd == "add":
        if len(sys.argv) < 3:
            print("Usage: graphx add <url> [--author Name] [--contributor Name] [--dir ./raw]", file=sys.stderr)
            sys.exit(1)
        from graphx.ingest import ingest as _ingest
        url = sys.argv[2]
        author: str | None = None
        contributor: str | None = None
        target_dir = Path("raw")
        args = sys.argv[3:]
        i = 0
        while i < len(args):
            if args[i] == "--author" and i + 1 < len(args):
                author = args[i + 1]; i += 2
            elif args[i] == "--contributor" and i + 1 < len(args):
                contributor = args[i + 1]; i += 2
            elif args[i] == "--dir" and i + 1 < len(args):
                target_dir = Path(args[i + 1]); i += 2
            else:
                i += 1
        try:
            saved = _ingest(url, target_dir, author=author, contributor=contributor)
            print(f"Saved to {saved}")
            print("Run /graphx --update in your AI assistant to update the graph.")
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)

    elif cmd == "watch":
        watch_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")
        if not watch_path.exists():
            print(f"error: path not found: {watch_path}", file=sys.stderr)
            sys.exit(1)
        from graphx.watch import watch as _watch
        try:
            _watch(watch_path)
        except ImportError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)

    elif cmd == "cluster-only":
        watch_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")
        no_viz = "--no-viz" in sys.argv
        _min_cs_arg = next((a for a in sys.argv if a.startswith("--min-community-size=")), None)
        min_community_size = int(_min_cs_arg.split("=")[1]) if _min_cs_arg else 3
        graph_json = watch_path / "graphx-out" / "graph.json"
        if not graph_json.exists():
            print(f"error: no graph found at {graph_json} — run /graphx first", file=sys.stderr)
            sys.exit(1)
        from networkx.readwrite import json_graph as _jg
        from graphx.build import build_from_json
        from graphx.cluster import cluster, score_all
        from graphx.analyze import god_nodes, surprising_connections, suggest_questions
        from graphx.report import generate
        from graphx.export import to_json, to_html, to_index_html
        print("Loading existing graph...")
        _raw = json.loads(graph_json.read_text(encoding="utf-8"))
        _directed = bool(_raw.get("directed", False))
        G = build_from_json(_raw, directed=_directed)
        print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print("Re-clustering...")
        communities = cluster(G)
        cohesion = score_all(G, communities)
        gods = god_nodes(G)
        surprises = surprising_connections(G, communities)
        labels = {cid: f"Community {cid}" for cid in communities}
        questions = suggest_questions(G, communities, labels)
        tokens = {"input": 0, "output": 0}
        report = generate(G, communities, cohesion, labels, gods, surprises,
                          {"warning": "cluster-only mode — file stats not available"},
                          tokens, str(watch_path), suggested_questions=questions,
                          min_community_size=min_community_size)
        out = watch_path / "graphx-out"
        (out / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")
        (out / ".graphx_version").write_text(__version__, encoding="utf-8")
        to_json(G, communities, str(out / "graph.json"))

        # Mirror watch.py pattern: gate to_html so core outputs (graph.json +
        # GRAPH_REPORT.md) always land. Honor --no-viz explicitly; otherwise
        # fall back to ValueError handling so an oversized graph doesn't crash
        # the CLI mid-write and leave a stale graph.html on disk.
        html_target = out / "graph.html"
        if no_viz:
            if html_target.exists():
                html_target.unlink()
            print(f"Done — {len(communities)} communities. GRAPH_REPORT.md and graph.json updated (--no-viz; graph.html removed).")
        else:
            try:
                to_html(G, communities, str(html_target), community_labels=labels or None)
                print(f"Done — {len(communities)} communities. GRAPH_REPORT.md, graph.json and graph.html updated.")
            except ValueError as viz_err:
                if html_target.exists():
                    html_target.unlink()
                print(f"Skipped graph.html: {viz_err}")
                print(f"Done — {len(communities)} communities. GRAPH_REPORT.md and graph.json updated.")
        
        # Generate activity.json for live dashboard polling
        try:
            from graphx.activity import save_activity
            activity_path = save_activity(str(watch_path), str(out), limit=50)
            print(f"activity.json written - live commit tracking")
        except Exception as act_err:
            print(f"Skipped activity.json: {act_err}")

        # Generate index.html dashboard with status data
        try:
            from graphx.status import generate_status_report
            status_report = generate_status_report(watch_path)
            to_index_html(
                G, communities, str(out),
                community_labels=labels or None,
                cohesion=cohesion,
                god_nodes_data=gods,
                status_report=status_report,
                project_name=watch_path.name,
            )
            print(f"index.html written - dashboard for all outputs")
        except Exception as idx_err:
            print(f"Skipped index.html: {idx_err}")

    elif cmd == "update":
        force = os.environ.get("GRAPHX_FORCE", "").lower() in ("1", "true", "yes")
        pull = False
        argv = list(sys.argv)
        if "--force" in argv[2:]:
            force = True
            argv = [a for a in argv if a != "--force"]
        if "--pull" in argv[2:]:
            pull = True
            argv = [a for a in argv if a != "--pull"]

        # If no path provided, update graphx package itself
        if len(argv) == 2 or (len(argv) == 3 and argv[2] in ("--force", "--pull")):
            self_update()
            sys.exit(0)

        # Otherwise, update project graph at the specified path
        if len(argv) > 2:
            # Find the path argument (skip flags)
            path_args = [a for a in argv[2:] if not a.startswith("--")]
            if path_args:
                watch_path = Path(path_args[0])
            else:
                watch_path = Path(".")
        else:
            # Try to recover the scan root saved by the last full build
            saved = Path(_GRAPHX_OUT) / ".graphx_root"
            if saved.exists():
                watch_path = Path(saved.read_text(encoding="utf-8").strip())
            else:
                watch_path = Path(".")
        if not watch_path.exists():
            print(f"error: path not found: {watch_path}", file=sys.stderr)
            sys.exit(1)

        # Git pull if requested
        if pull:
            git_dir = watch_path / ".git"
            if git_dir.exists():
                print("Pulling latest changes from git...")
                import subprocess
                try:
                    result = subprocess.run(
                        ["git", "pull"],
                        cwd=watch_path,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    if result.returncode == 0:
                        print("Git pull successful.")
                        if result.stdout:
                            print(result.stdout)
                    else:
                        print(f"Git pull failed: {result.stderr}", file=sys.stderr)
                        print("Continuing with update anyway...", file=sys.stderr)
                except subprocess.TimeoutExpired:
                    print("Git pull timed out. Continuing with update...", file=sys.stderr)
                except Exception as e:
                    print(f"Git pull error: {e}", file=sys.stderr)
                    print("Continuing with update anyway...", file=sys.stderr)
            else:
                print("Not a git repository (no .git directory). Skipping pull.", file=sys.stderr)

        from graphx.watch import _rebuild_code
        print(f"Re-extracting code files in {watch_path} (no LLM needed)...")
        ok = _rebuild_code(watch_path, force=force)
        if ok:
            print("Code graph updated. For doc/paper/image changes run /graphx --update in your AI assistant.")
            if not os.environ.get("MOONSHOT_API_KEY") and not os.environ.get("GRAPHX_NO_TIPS"):
                print("Tip: set MOONSHOT_API_KEY to use Kimi K2.6 for semantic extraction — 3x cheaper, richer graphs. pip install 'graphx[kimi]'")
        else:
            print("Nothing to update or rebuild failed — check output above.", file=sys.stderr)
            sys.exit(1)

    elif cmd == "hook-check":
        # Codex Desktop rejects hookSpecificOutput.additionalContext on PreToolUse.
        # Keep this as a cross-platform no-op so installed hooks never break Bash
        # tool calls. Graph guidance reaches the agent via AGENTS.md / skill instead.
        sys.exit(0)
    elif cmd == "check-update":
        if len(sys.argv) < 3:
            print("Usage: graphx check-update <path>", file=sys.stderr)
            sys.exit(1)
        from graphx.watch import check_update
        check_update(Path(sys.argv[2]).resolve())
        sys.exit(0)
    elif cmd == "log":
        if len(sys.argv) < 3:
            print("Usage: graphx log <title> --description <desc> --files <files> --tags <tags>", file=sys.stderr)
            sys.exit(1)
        
        from graphx.changelog import Changelog
        
        title = sys.argv[2]
        description = ""
        files_arg = ""
        tags_arg = ""
        
        args = sys.argv[3:]
        i = 0
        while i < len(args):
            if args[i].startswith("--description="):
                description = args[i].replace("--description=", "")
            elif args[i] == "--description" and i + 1 < len(args):
                description = args[i + 1]
                i += 1
            elif args[i].startswith("--files="):
                files_arg = args[i].replace("--files=", "")
            elif args[i] == "--files" and i + 1 < len(args):
                files_arg = args[i + 1]
                i += 1
            elif args[i].startswith("--tags="):
                tags_arg = args[i].replace("--tags=", "")
            elif args[i] == "--tags" and i + 1 < len(args):
                tags_arg = args[i + 1]
                i += 1
            i += 1
        
        # Parse files
        files_changed = []
        if files_arg:
            for file_path in files_arg.split(","):
                file_path = file_path.strip()
                if file_path:
                    files_changed.append({
                        "file": file_path,
                        "action": "modified",
                        "lines_added": 0,
                        "lines_removed": 0,
                        "nodes_added": 0,
                        "nodes_removed": 0
                    })
        
        # Parse tags
        tags = [t.strip() for t in tags_arg.split(",")] if tags_arg else []
        
        # Get output directory
        output_dir = Path(_GRAPHX_OUT)
        
        # Add session
        changelog = Changelog(output_dir)
        session_id = changelog.add_session(title, description, files_changed, tags)
        
        print(f"[OK] Session logged: {session_id}")
        print(f"  Title: {title}")
        print(f"  Files: {len(files_changed)}")
        print(f"  Tags: {', '.join(tags) if tags else 'none'}")
        print(f"  Saved to: {output_dir / 'changelog.json'}")
        sys.exit(0)
    elif cmd == "tree":
        # Emit a D3 v7 collapsible-tree HTML view of graph.json:
        # expand-all / collapse-all / reset-view buttons, multi-line
        # wrapText labels with separately-coloured name + count,
        # depth-based palette, click-to-toggle subtree, hover inspector
        # showing top-K outbound edges per symbol.
        from typing import Optional as _Opt
        from graphx.tree_html import write_tree_html, DEFAULT_MAX_CHILDREN
        graph_path = Path(_GRAPHX_OUT) / "graph.json"
        output_path: "_Opt[Path]" = None
        root: "_Opt[str]" = None
        max_children = DEFAULT_MAX_CHILDREN
        top_k_edges = 0
        project_label: "_Opt[str]" = None
        args = sys.argv[2:]
        i_arg = 0
        while i_arg < len(args):
            a = args[i_arg]
            if a == "--graph" and i_arg + 1 < len(args):
                graph_path = Path(args[i_arg + 1]); i_arg += 2
            elif a == "--output" and i_arg + 1 < len(args):
                output_path = Path(args[i_arg + 1]); i_arg += 2
            elif a == "--root" and i_arg + 1 < len(args):
                root = args[i_arg + 1]; i_arg += 2
            elif a == "--max-children" and i_arg + 1 < len(args):
                max_children = int(args[i_arg + 1]); i_arg += 2
            elif a == "--top-k-edges" and i_arg + 1 < len(args):
                top_k_edges = int(args[i_arg + 1]); i_arg += 2
            elif a == "--label" and i_arg + 1 < len(args):
                project_label = args[i_arg + 1]; i_arg += 2
            elif a in ("-h", "--help"):
                print("Usage: graphx tree [--graph PATH] [--output HTML]")
                print("  --graph PATH         path to graph.json (default graphx-out/graph.json)")
                print("  --output HTML        output path (default graphx-out/GRAPH_TREE.html)")
                print("  --root PATH          filesystem root (default: longest common dir of all source_files)")
                print("  --max-children N     cap visible children per node (default 200)")
                print("  --top-k-edges N      pre-compute top-K outbound edges per symbol (default 12)")
                print("  --label NAME         project label shown in the page header")
                return
            else:
                i_arg += 1
        if not graph_path.is_file():
            print(f"error: graph.json not found at {graph_path}", file=sys.stderr)
            sys.exit(1)
        if output_path is None:
            output_path = graph_path.parent / "GRAPH_TREE.html"
        out = write_tree_html(
            graph_path=graph_path, output_path=output_path,
            root=root, max_children=max_children,
            top_k_edges=top_k_edges, project_label=project_label,
        )
        size_kb = out.stat().st_size / 1024
        print(f"wrote {out} ({size_kb:.1f} KB)")
        print(f"open with: xdg-open {out}  (or file://{out.resolve()})")
        sys.exit(0)

    elif cmd == "index":
        # Generate index.html dashboard for graphx outputs
        from networkx.readwrite import json_graph as _jg
        from graphx.build import build_from_json
        from graphx.analyze import god_nodes
        from graphx.export import to_index_html
        graph_path = Path(_GRAPHX_OUT) / "graph.json"
        output_dir = graph_path.parent
        args = sys.argv[2:]
        i_arg = 0
        project_name = None
        while i_arg < len(args):
            a = args[i_arg]
            if a == "--graph" and i_arg + 1 < len(args):
                graph_path = Path(args[i_arg + 1]); i_arg += 2
                output_dir = graph_path.parent
            elif a == "--output" and i_arg + 1 < len(args):
                output_dir = Path(args[i_arg + 1]); i_arg += 2
            elif a == "--name" and i_arg + 1 < len(args):
                project_name = args[i_arg + 1]; i_arg += 2
            elif a in ("-h", "--help"):
                print("Usage: graphx index [--graph PATH] [--output DIR] [--name NAME]")
                print("  --graph PATH         path to graph.json (default graphx-out/graph.json)")
                print("  --output DIR         output directory (default: same as graph.json)")
                print("  --name NAME          project name for the dashboard title")
                return
            else:
                i_arg += 1
        if not graph_path.is_file():
            print(f"error: graph.json not found at {graph_path}", file=sys.stderr)
            sys.exit(1)
        try:
            _raw = json.loads(graph_path.read_text(encoding="utf-8"))
            G = _jg.node_link_graph(_raw, edges="links")
        except TypeError:
            G = _jg.node_link_graph(_raw)
        
        # Load labels and analysis if available
        labels_path = output_dir / ".graphx_labels.json"
        analysis_path = output_dir / ".graphx_analysis.json"
        labels = None
        cohesion = None
        gods = None
        if labels_path.exists():
            labels = {int(k): v for k, v in json.loads(labels_path.read_text()).items()}
        if analysis_path.exists():
            analysis = json.loads(analysis_path.read_text())
            cohesion = {int(k): v for k, v in analysis.get("cohesion", {}).items()}
            gods = analysis.get("gods", [])
        else:
            gods = god_nodes(G)
        
        # Reconstruct communities from graph
        node_community = {}
        for nid, data in G.nodes(data=True):
            cid = data.get("community")
            if cid is not None:
                node_community[nid] = cid
        communities = {}
        for nid, cid in node_community.items():
            communities.setdefault(cid, []).append(nid)
        
        to_index_html(G, communities, str(output_dir), community_labels=labels, cohesion=cohesion, god_nodes_data=gods, project_name=project_name)
        print(f"index.html written to {output_dir / 'index.html'}")
        sys.exit(0)

    elif cmd == "capture-commit":
        from graphx.hooks import capture_commit
        repo_path = Path('.')
        commit_data = capture_commit(repo_path)
        if commit_data:
            print(f"[graphx] Captured commit: {commit_data['hash']} by {commit_data['author']} ({commit_data['source']})")
            print(f"[graphx] Files changed: {len(commit_data['files_changed'])}")
        else:
            print("[graphx] No commit to capture or git repository not found")
        sys.exit(0)

    elif cmd == "status":
        from graphx.status import generate_status_report, print_status_dashboard
        repo_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")
        report = generate_status_report(repo_path)
        print_status_dashboard(report)
        sys.exit(0)

    elif cmd == "merge-graphs":
        # graphx merge-graphs graph1.json graph2.json ... --out merged.json
        args = sys.argv[2:]
        graph_paths: list[Path] = []
        out_path = Path(_GRAPHX_OUT) / "merged-graph.json"
        i = 0
        while i < len(args):
            if args[i] == "--out" and i + 1 < len(args):
                out_path = Path(args[i + 1]); i += 2
            else:
                graph_paths.append(Path(args[i])); i += 1
        if len(graph_paths) < 2:
            print("Usage: graphx merge-graphs <graph1.json> <graph2.json> [...] [--out merged.json]", file=sys.stderr)
            sys.exit(1)
        import networkx as _nx
        from networkx.readwrite import json_graph as _jg
        graphs = []
        for gp in graph_paths:
            if not gp.exists():
                print(f"error: not found: {gp}", file=sys.stderr)
                sys.exit(1)
            data = json.loads(gp.read_text(encoding="utf-8"))
            try:
                G = _jg.node_link_graph(data, edges="links")
            except TypeError:
                G = _jg.node_link_graph(data)
            # Tag every node with which repo it came from
            repo_tag = gp.parent.parent.name  # graphx-out/../ → repo dir name
            for node in G.nodes:
                G.nodes[node].setdefault("repo", repo_tag)
            graphs.append(G)
        merged = _nx.compose_all(graphs)
        try:
            out_data = _jg.node_link_data(merged, edges="links")
        except TypeError:
            out_data = _jg.node_link_data(merged)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(out_data, indent=2), encoding="utf-8")
        print(f"Merged {len(graphs)} graphs → {merged.number_of_nodes()} nodes, {merged.number_of_edges()} edges")
        print(f"Written to: {out_path}")

    elif cmd == "clone":
        if len(sys.argv) < 3:
            print("Usage: graphx clone <github-url> [--branch <branch>] [--out <dir>]", file=sys.stderr)
            sys.exit(1)
        url = sys.argv[2]
        branch: str | None = None
        out_dir: Path | None = None
        args = sys.argv[3:]
        i = 0
        while i < len(args):
            if args[i] == "--branch" and i + 1 < len(args):
                branch = args[i + 1]; i += 2
            elif args[i] == "--out" and i + 1 < len(args):
                out_dir = Path(args[i + 1]); i += 2
            else:
                i += 1
        local_path = _clone_repo(url, branch=branch, out_dir=out_dir)
        print(local_path)

    elif cmd == "benchmark":
        from graphx.benchmark import run_benchmark, print_benchmark
        graph_path = sys.argv[2] if len(sys.argv) > 2 else "graphx-out/graph.json"
        # Try to load corpus_words from detect output
        corpus_words = None
        detect_path = Path(".graphx_detect.json")
        if detect_path.exists():
            try:
                detect_data = json.loads(detect_path.read_text(encoding="utf-8"))
                corpus_words = detect_data.get("total_words")
            except Exception:
                pass
        result = run_benchmark(graph_path, corpus_words=corpus_words)
        print_benchmark(result)
    else:
        print(f"error: unknown command '{cmd}'", file=sys.stderr)
        print("Run 'graphx --help' for usage.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
