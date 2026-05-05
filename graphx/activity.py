# Real-time activity tracking for Ai-GraphX dashboard
"""
Generates activity.json from git history.
This file is consumed by index.html for live activity timeline rendering.
"""
import json
from pathlib import Path
from datetime import datetime, timezone

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False


def _is_ai_commit(commit_message: str, author_name: str, author_email: str) -> bool:
    """Detect if a commit was authored by an AI coding assistant."""
    text = f"{commit_message} {author_name} {author_email}".lower()
    ai_markers = [
        "devin-ai-integration",
        "devin",
        "claude",
        "copilot",
        "cursor",
        "ai-generated",
        "auto-generated",
        "generated with",
        "gstack",
        "github-actions",
        "dependabot",
        "renovate",
    ]
    return any(marker in text for marker in ai_markers)


def get_recent_activity(repo_path: str, limit: int = 50) -> dict:
    """Extract recent git commits with file-change detail for the activity timeline.

    Returns a dict shaped like:
    {
      "commits": [
        {
          "hash": "abc1234...",
          "short_hash": "abc1234",
          "author": "Name",
          "email": "name@example.com",
          "date": "2026-05-05T10:00:00+00:00",
          "message": "Fix bug",
          "source": "ai" | "user",
          "files_changed": [
            {"file": "src/main.py", "insertions": 10, "deletions": 2, "lines": 12}
          ],
          "total_files": 1,
          "total_insertions": 10,
          "total_deletions": 2,
          "total_lines": 12,
        }
      ],
      "total_commits": 1,
      "generated_at": "..."
    }
    """
    if not GIT_AVAILABLE:
        return {
            "commits": [],
            "total_commits": 0,
            "error": "gitpython not installed",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    try:
        repo = git.Repo(repo_path)
    except Exception as exc:
        return {
            "commits": [],
            "total_commits": 0,
            "error": f"not a git repo: {exc}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    commits_data = []
    try:
        for commit in repo.iter_commits("HEAD", max_count=limit):
            stats = commit.stats
            # Build a map of file -> change_type from diff for accurate action labels
            action_map: dict[str, str] = {}
            try:
                diff_list = commit.diff(commit.parents[0]) if commit.parents else commit.diff(git.NULL_TREE)
                for d in diff_list:
                    path = d.a_path or d.b_path
                    if not path:
                        continue
                    # git diff change_type: 'A'=added, 'D'=deleted, 'M'=modified, 'R'=renamed, 'T'=type change
                    ctype = d.change_type or "M"
                    action_map[path] = {"A": "added", "D": "deleted", "R": "renamed", "T": "modified", "M": "modified"}.get(ctype, "modified")
            except Exception:
                pass  # fall back to stats-only (no action/size)

            files_changed = []
            for file_path, file_stats in stats.files.items():
                files_changed.append(
                    {
                        "file": file_path,
                        "action": action_map.get(file_path, "modified"),
                        "size": file_stats.get("lines", 0) * 50,  # rough bytes estimate from line count
                        "insertions": file_stats.get("insertions", 0),
                        "deletions": file_stats.get("deletions", 0),
                        "lines": file_stats.get("lines", 0),
                    }
                )

            commits_data.append(
                {
                    "hash": commit.hexsha,
                    "short_hash": commit.hexsha[:7],
                    "author": commit.author.name,
                    "email": commit.author.email,
                    "date": commit.committed_datetime.isoformat(),
                    "message": commit.message.strip(),
                    "source": "ai"
                    if _is_ai_commit(commit.message, commit.author.name, commit.author.email)
                    else "user",
                    "files_changed": files_changed,
                    "total_files": len(files_changed),
                    "total_insertions": stats.total.get("insertions", 0),
                    "total_deletions": stats.total.get("deletions", 0),
                    "total_lines": stats.total.get("lines", 0),
                }
            )
    except Exception as exc:
        return {
            "commits": [],
            "total_commits": 0,
            "error": str(exc),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    return {
        "commits": commits_data,
        "total_commits": len(commits_data),
        "staged": _get_staged_changes(repo_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _get_staged_changes(repo_path: str) -> list:
    """Get files that are staged but not committed."""
    if not GIT_AVAILABLE:
        return []
    try:
        repo = git.Repo(repo_path)
        staged = []
        # Diff HEAD against index to find what's staged
        diff = repo.index.diff("HEAD")
        for change in diff:
            path = change.a_path or change.b_path
            if not path:
                continue
            ctype = change.change_type or "M"
            action = {"A": "added", "D": "deleted", "R": "renamed", "T": "modified", "M": "modified"}.get(ctype, "modified")
            staged.append({
                "file": path,
                "action": action,
                "date": datetime.now(timezone.utc).isoformat(),
                "source": "user"
            })
        return staged
    except Exception:
        return []


def save_activity(repo_path: str, output_dir: str, limit: int = 50) -> Path:
    """Generate activity.json and write it to the graphx output directory.

    Returns the path to the written file.
    """
    activity = get_recent_activity(repo_path, limit=limit)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    activity_file = out / "activity.json"
    activity_file.write_text(
        json.dumps(activity, indent=2, default=str),
        encoding="utf-8",
    )
    return activity_file
