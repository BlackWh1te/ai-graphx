# Work session tracking and changelog management
from pathlib import Path
from datetime import datetime, timezone
import json
from typing import List, Dict, Optional


class Changelog:
    """Manage work sessions and changelog for programmer summary."""
    
    def __init__(self, output_dir: Path):
        """Initialize changelog with output directory."""
        self.file = output_dir / "changelog.json"
        self.data = self._load()
    
    def _load(self) -> Dict:
        """Load changelog from file, or create empty structure."""
        if self.file.exists():
            try:
                return json.loads(self.file.read_text())
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, start fresh
                return {"sessions": []}
        return {"sessions": []}
    
    def _save(self):
        """Save changelog to file."""
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps(self.data, indent=2))
    
    def add_session(
        self,
        title: str,
        description: str,
        files_changed: List[Dict],
        tags: Optional[List[str]] = None
    ) -> str:
        """Add a new work session to the changelog.
        
        Args:
            title: Title of the work session (e.g., "Add authentication system")
            description: Description of what was done
            files_changed: List of file change dicts with keys:
                - file: file path
                - action: "added", "modified", or "deleted"
                - lines_added: number of lines added (optional, default 0)
                - lines_removed: number of lines removed (optional, default 0)
                - nodes_added: number of nodes added (optional, default 0)
                - nodes_removed: number of nodes removed (optional, default 0)
            tags: List of tags (e.g., ["feature", "auth", "security"])
        
        Returns:
            Session ID (e.g., "feat-001")
        """
        # Calculate metrics
        metrics = {
            "total_files": len(files_changed),
            "lines_added": sum(f.get("lines_added", 0) for f in files_changed),
            "lines_removed": sum(f.get("lines_removed", 0) for f in files_changed),
            "nodes_added": sum(f.get("nodes_added", 0) for f in files_changed),
            "nodes_removed": sum(f.get("nodes_removed", 0) for f in files_changed),
        }
        
        session_id = f"feat-{len(self.data['sessions']) + 1:03d}"
        
        session = {
            "id": session_id,
            "title": title,
            "description": description,
            "date": datetime.now(timezone.utc).isoformat(),
            "files_changed": files_changed,
            "metrics": metrics,
            "tags": tags or []
        }
        
        self.data["sessions"].append(session)
        self._save()
        return session_id
    
    def get_sessions(
        self,
        filter_tags: Optional[List[str]] = None,
        days: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Get sessions with optional filtering.
        
        Args:
            filter_tags: Only return sessions with these tags
            days: Only return sessions from last N days
            limit: Maximum number of sessions to return
        
        Returns:
            List of session dicts, sorted by date descending
        """
        sessions = self.data["sessions"].copy()
        
        # Filter by tags
        if filter_tags:
            sessions = [s for s in sessions if any(t in s["tags"] for t in filter_tags)]
        
        # Filter by date
        if days:
            cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)
            sessions = [s for s in sessions if datetime.fromisoformat(s["date"]).timestamp() > cutoff]
        
        # Sort by date descending
        sessions.sort(key=lambda x: x["date"], reverse=True)
        
        # Apply limit
        if limit:
            sessions = sessions[:limit]
        
        return sessions
    
    def get_summary_stats(self, days: Optional[int] = None) -> Dict:
        """Get summary statistics for all sessions.
        
        Args:
            days: Only include sessions from last N days
        
        Returns:
            Dict with stats: total_sessions, total_files, lines_added, etc.
        """
        sessions = self.get_sessions(days=days)
        
        return {
            "total_sessions": len(sessions),
            "total_files": sum(s["metrics"]["total_files"] for s in sessions),
            "lines_added": sum(s["metrics"]["lines_added"] for s in sessions),
            "lines_removed": sum(s["metrics"]["lines_removed"] for s in sessions),
            "nodes_added": sum(s["metrics"]["nodes_added"] for s in sessions),
            "nodes_removed": sum(s["metrics"]["nodes_removed"] for s in sessions),
        }
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID.
        
        Args:
            session_id: Session ID to delete (e.g., "feat-001")
        
        Returns:
            True if deleted, False if not found
        """
        for i, session in enumerate(self.data["sessions"]):
            if session["id"] == session_id:
                del self.data["sessions"][i]
                self._save()
                return True
        return False
    
    def clear_all(self):
        """Clear all sessions (use with caution)."""
        self.data = {"sessions": []}
        self._save()
