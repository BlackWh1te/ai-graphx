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
            files_changed = []
            for file_path, file_stats in stats.files.items():
                files_changed.append(
                    {
                        "file": file_path,
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
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


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
