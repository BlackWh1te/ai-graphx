# Project status analysis and reporting
import json
from pathlib import Path
from datetime import datetime, timezone
import os

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False

def detect_external_files(repo_path):
    """Detect files that exist but have no git history (drag & drop)."""
    if not GIT_AVAILABLE:
        return []
    
    try:
        repo = git.Repo(repo_path)
    except:
        return []
    
    # Get all tracked files
    tracked_files = set()
    try:
        for commit in repo.iter_commits('HEAD'):
            for item in commit.tree.traverse():
                if item.type == 'blob':
                    tracked_files.add(item.path)
    except:
        pass
    
    # Get all files in working directory
    all_files = set()
    for root, dirs, files in os.walk(repo_path):
        # Skip .git and graphx-out
        dirs[:] = [d for d in dirs if d not in ['.git', 'graphx-out', '__pycache__', '.venv', 'venv', 'node_modules']]
        for file in files:
            full_path = Path(root) / file
            rel_path = str(full_path.relative_to(repo_path))
            all_files.add(rel_path)
    
    # External files = files that exist but aren't tracked
    external = all_files - tracked_files
    
    # Add metadata
    external_files = []
    for file_path in external:
        full_path = Path(repo_path) / file_path
        try:
            stat = full_path.stat()
            external_files.append({
                'file': file_path,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            })
        except:
            external_files.append({
                'file': file_path,
                'size': 0,
                'created': None,
                'modified': None,
            })
    
    return external_files

def detect_large_files(repo_path, threshold_mb=10):
    """Detect files larger than threshold (default 10MB)."""
    large_files = []
    threshold_bytes = threshold_mb * 1024 * 1024
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ['.git', 'graphx-out', '__pycache__', '.venv', 'venv', 'node_modules']]
        for file in files:
            full_path = Path(root) / file
            try:
                size = full_path.stat().st_size
                if size > threshold_bytes:
                    rel_path = str(full_path.relative_to(repo_path))
                    large_files.append({
                        'file': rel_path,
                        'size': size,
                        'size_mb': size / (1024 * 1024)
                    })
            except:
                pass
    
    return sorted(large_files, key=lambda x: x['size'], reverse=True)

def get_branch_status(repo_path):
    """Get branch-specific information."""
    if not GIT_AVAILABLE:
        return {'current': 'git_not_available', 'all': [], 'untracked': []}
    
    try:
        repo = git.Repo(repo_path)
    except:
        return {'current': 'not_a_git_repo', 'all': [], 'untracked': []}
    
    # Get current branch
    try:
        current_branch = repo.active_branch.name
    except:
        try:
            current_branch = repo.head.reference.name
        except:
            current_branch = 'detached'
    
    # Get all branches
    all_branches = [head.name for head in repo.heads]
    
    # Get untracked branches (branches not on remote)
    untracked = []
    try:
        remote_refs = repo.remotes.origin.refs if 'origin' in repo.remotes else []
        remote_branches = set(ref.name.split('/')[-1] for ref in remote_refs)
        untracked = [b for b in all_branches if b not in remote_branches]
    except:
        pass
    
    # Get commits per branch
    branch_commits = {}
    for branch_name in all_branches:
        try:
            branch = repo.heads[branch_name]
            commit_count = sum(1 for _ in repo.iter_commits(branch, max_count=1000))
            branch_commits[branch_name] = commit_count
        except:
            branch_commits[branch_name] = 0
    
    return {
        'current': current_branch,
        'all': all_branches,
        'untracked': untracked,
        'commits_per_branch': branch_commits
    }

def get_staged_changes(repo_path):
    """Get files that are staged but not committed."""
    if not GIT_AVAILABLE:
        return []
    
    try:
        repo = git.Repo(repo_path)
    except:
        return []
    
    staged = []
    
    try:
        # Get staged changes
        diff = repo.index.diff("HEAD")
        
        for change in diff:
            file_path = change.a_path if change.a_path else change.b_path
            if not file_path:
                continue
            
            action = 'modified'
            if change.new_file:
                action = 'added'
            elif change.deleted_file:
                action = 'deleted'
            
            # Get file size
            full_path = Path(repo_path) / file_path
            file_size = full_path.stat().st_size if full_path.exists() else 0
            
            staged.append({
                'file': file_path,
                'action': action,
                'size': file_size
            })
    except:
        pass
    
    return staged

def get_merge_commits(repo_path, limit=20):
    """Get recent merge commits."""
    if not GIT_AVAILABLE:
        return []
    
    try:
        repo = git.Repo(repo_path)
    except:
        return []
    
    merge_commits = []
    
    try:
        for commit in repo.iter_commits('HEAD', max_count=limit * 2):  # Get more to filter
            if len(commit.parents) > 1:  # Merge commit
                merge_commits.append({
                    'hash': commit.hexsha[:7],
                    'full_hash': commit.hexsha,
                    'author': commit.author.name,
                    'date': commit.committed_datetime.isoformat(),
                    'message': commit.message.strip(),
                    'parents': [p.hexsha[:7] for p in commit.parents]
                })
                
                if len(merge_commits) >= limit:
                    break
    except:
        pass
    
    return merge_commits

def load_commits(repo_path):
    """Load commits from commits.json, falling back to activity.json."""
    commits_file = Path(repo_path) / 'graphx-out' / 'commits.json'
    if commits_file.exists():
        try:
            data = json.loads(commits_file.read_text())
            commits = data.get('commits', [])
            if commits:
                return commits
        except:
            pass

    # Fallback: activity.json has full git history from save_activity()
    activity_file = Path(repo_path) / 'graphx-out' / 'activity.json'
    if activity_file.exists():
        try:
            data = json.loads(activity_file.read_text())
            return data.get('commits', [])
        except:
            pass

    return []

def group_commits_by_source(commits, days=7):
    """Group commits by source and filter by time range."""
    cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)
    
    filtered = [c for c in commits if datetime.fromisoformat(c['date']).timestamp() > cutoff]
    
    grouped = {'ai': [], 'user': [], 'external': []}
    for commit in filtered:
        source = commit.get('source', 'user')
        if source in grouped:
            grouped[source].append(commit)
    
    return grouped

def get_hot_files(commits, threshold=5):
    """Get files that appear in multiple commits."""
    file_counts = {}
    
    for commit in commits:
        for file_change in commit.get('files_changed', []):
            file_path = file_change['file']
            file_counts[file_path] = file_counts.get(file_path, 0) + 1
    
    # Filter by threshold
    hot_files = {file: count for file, count in file_counts.items() if count >= threshold}
    
    # Get last commit for each hot file
    hot_file_details = []
    for file_path, count in hot_files.items():
        last_commit = None
        for commit in commits:
            for file_change in commit.get('files_changed', []):
                if file_change['file'] == file_path:
                    last_commit = commit
                    break
            if last_commit:
                break
        
        hot_file_details.append({
            'file': file_path,
            'commit_count': count,
            'last_commit': last_commit
        })
    
    return sorted(hot_file_details, key=lambda x: x['commit_count'], reverse=True)

def calculate_change_velocity(commits, days=7):
    """Calculate change velocity metrics."""
    cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)
    
    recent_commits = [c for c in commits if datetime.fromisoformat(c['date']).timestamp() > cutoff]
    
    # Group by day
    daily_counts = {}
    for commit in recent_commits:
        date = datetime.fromisoformat(commit['date']).date().isoformat()
        daily_counts[date] = daily_counts.get(date, 0) + 1
    
    return {
        'total_commits': len(recent_commits),
        'daily_counts': daily_counts,
        'average_per_day': len(recent_commits) / max(len(daily_counts), 1)
    }

def get_graph_status(repo_path):
    """Check graph health and statistics."""
    graph_out = Path(repo_path) / 'graphx-out'
    graph_json = graph_out / 'graph.json'
    report_md = graph_out / 'GRAPH_REPORT.md'
    cost_json = graph_out / 'cost.json'
    needs_update = graph_out / '.needs_update'

    graph_info = {
        'exists': False,
        'nodes': 0,
        'edges': 0,
        'communities': 0,
        'last_build': None,
        'total_runs': 0,
        'total_input_tokens': 0,
        'total_output_tokens': 0,
        'needs_update': False,
        'watch_active': False
    }

    if graph_json.exists():
        try:
            data = json.loads(graph_json.read_text())
            graph_info['exists'] = True
            graph_info['nodes'] = len(data.get('nodes', []))
            graph_info['edges'] = len(data.get('links', []))
            graph_info['communities'] = len(set(n.get('community', 0) for n in data.get('nodes', [])))
        except:
            pass

    if report_md.exists():
        try:
            stat = report_md.stat()
            graph_info['last_build'] = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
        except:
            pass

    if cost_json.exists():
        try:
            cost_data = json.loads(cost_json.read_text())
            graph_info['total_runs'] = len(cost_data.get('runs', []))
            graph_info['total_input_tokens'] = cost_data.get('total_input_tokens', 0)
            graph_info['total_output_tokens'] = cost_data.get('total_output_tokens', 0)
        except:
            pass

    graph_info['needs_update'] = needs_update.exists()

    return graph_info

def generate_status_report(repo_path):
    """Generate comprehensive status report."""
    if not Path(repo_path).exists():
        return {'error': 'Path does not exist'}

    # Load commits
    commits = load_commits(repo_path)

    # Detect external files
    external_files = detect_external_files(repo_path)

    # Detect large files
    large_files = detect_large_files(repo_path)

    # Get branch status
    branch_status = get_branch_status(repo_path)

    # Get staged changes
    staged_changes = get_staged_changes(repo_path)

    # Get merge commits
    merge_commits = get_merge_commits(repo_path)

    # Group commits by source
    grouped_commits = group_commits_by_source(commits)

    # Get hot files
    hot_files = get_hot_files(commits)

    # Calculate velocity
    velocity = calculate_change_velocity(commits)

    # Get graph status
    graph_status = get_graph_status(repo_path)

    return {
        'repo_path': str(repo_path),
        'is_git_repo': (Path(repo_path) / '.git').exists(),
        'commits': commits,
        'grouped_commits': grouped_commits,
        'external_files': external_files,
        'large_files': large_files,
        'branch_status': branch_status,
        'staged_changes': staged_changes,
        'merge_commits': merge_commits,
        'hot_files': hot_files,
        'velocity': velocity,
        'graph_status': graph_status,
        'generated_at': datetime.now(timezone.utc).isoformat()
    }

def print_status_dashboard(report):
    """Print the status dashboard to terminal."""
    if 'error' in report:
        print(f"Error: {report['error']}")
        return
    
    print("=" * 65)
    print("Project Status Dashboard")
    print("=" * 65)
    print()

    print(f"Project: {report['repo_path']}")
    print(f"Generated: {report['generated_at']}")
    print(f"Git Repo: {'Yes' if report['is_git_repo'] else 'No'}")
    print()

    # Graph Status
    graph = report['graph_status']
    print("+-" + "-" * 63 + "-+")
    print("| Graph Status".ljust(63) + "|")
    print("+-" + "-" * 63 + "-+")
    if graph['exists']:
        status = "OK"
        if graph['needs_update']:
            status = "NEEDS UPDATE"
        print(f"| Status: {status:<53}")
        print(f"| Nodes: {graph['nodes']:<54}")
        print(f"| Edges: {graph['edges']:<54}")
        print(f"| Communities: {graph['communities']:<50}")
        print(f"| Total runs: {graph['total_runs']:<51}")
        if graph['last_build']:
            last = datetime.fromisoformat(graph['last_build']).strftime('%Y-%m-%d %H:%M')
            print(f"| Last build: {last:<50}")
        if graph['total_input_tokens'] > 0 or graph['total_output_tokens'] > 0:
            print(f"| Total tokens: {graph['total_input_tokens'] + graph['total_output_tokens']:,} ({graph['total_input_tokens']:,} in / {graph['total_output_tokens']:,} out)")
        print()
    else:
        print("| No graph found - run 'graphx .' to build one".ljust(63) + "|")
        print()

    print("+-" + "-" * 63 + "-+")
    print()

    # Change Summary
    print("+-" + "-" * 63 + "-+")
    print("| Change Summary (Last 7 days)".ljust(63) + "|")
    print("+-" + "-" * 63 + "-+")
    
    grouped = report['grouped_commits']
    for source, commits in grouped.items():
        emoji = {'ai': '[AI]', 'user': '[USER]', 'external': '[EXT]'}[source]
        color = {'ai': '[BLUE]', 'user': '[GREEN]', 'external': '[ORANGE]'}[source]
        
        file_count = sum(len(c.get('files_changed', [])) for c in commits)
        
        if commits:
            latest = commits[0]
            date = datetime.fromisoformat(latest['date']).strftime('%Y-%m-%d %H:%M')
            print(f"| {emoji} {source.title():<13} {file_count:<10} files")
            print(f"|    Latest: {latest['hash']:<8} {date:<17} {color}")
            print()
        else:
            print(f"| {emoji} {source.title():<13} 0 files")
            print()
    
    print("+-" + "-" * 63 + "-+")
    print()
    
    # External Files
    if report['external_files']:
        print("+-" + "-" * 63 + "-+")
        print("| External Files (Untracked)".ljust(63) + "|")
        print("+-" + "-" * 63 + "-+")
        
        for ext_file in report['external_files'][:10]:
            size_mb = ext_file['size'] / (1024 * 1024)
            date = datetime.fromisoformat(ext_file['created']).strftime('%Y-%m-%d %H:%M') if ext_file['created'] else 'N/A'
            print(f"| [EXT] {ext_file['file']:<50}")
            print(f"|    Added: {date:<20} Size: {size_mb:.2f} MB")
            print()
        
        if len(report['external_files']) > 10:
            print(f"| ... and {len(report['external_files']) - 10} more external files")
            print()
        
        print("+-" + "-" * 63 + "-+")
        print()
    
    # Large Files
    if report['large_files']:
        print("+-" + "-" * 63 + "-+")
        print("| Large Files (>10MB)".ljust(63) + "|")
        print("+-" + "-" * 63 + "-+")
        
        for large_file in report['large_files'][:5]:
            print(f"| [LARGE] {large_file['file']:<50}")
            print(f"|    Size: {large_file['size_mb']:.2f} MB")
            print()
        
        if len(report['large_files']) > 5:
            print(f"| ... and {len(report['large_files']) - 5} more large files")
            print()
        
        print("+-" + "-" * 63 + "-+")
        print()
    
    # Branch Status
    if report['is_git_repo']:
        print("+-" + "-" * 63 + "-+")
        print("| Branch Status".ljust(63) + "|")
        print("+-" + "-" * 63 + "-+")
        
        branch_status = report['branch_status']
        print(f"| Current: {branch_status['current']:<53}")
        print(f"| Total branches: {len(branch_status['all']):<47}")
        print(f"| Untracked branches: {len(branch_status['untracked']):<45}")
        print()
        
        if branch_status['untracked']:
            print("| Untracked branches:")
            for branch in branch_status['untracked'][:5]:
                commits = branch_status['commits_per_branch'].get(branch, 0)
                print(f"|   {branch:<40} ({commits} commits)")
            
            if len(branch_status['untracked']) > 5:
                print(f"|   ... and {len(branch_status['untracked']) - 5} more")
            print()
        
        print("+-" + "-" * 63 + "-+")
        print()
    
    # Staged Changes
    if report['staged_changes']:
        print("+-" + "-" * 63 + "-+")
        print("| [STAGED] Staged Changes (Not Committed)".ljust(63) + "|")
        print("+-" + "-" * 63 + "-+")
        
        for staged in report['staged_changes'][:10]:
            action_emoji = {'added': '[+]', 'modified': '[M]', 'deleted': '[D]'}[staged['action']]
            print(f"| {action_emoji} {staged['file']:<50}")
            print(f"|    Action: {staged['action']:<20} Size: {staged['size']:,} bytes")
            print()
        
        if len(report['staged_changes']) > 10:
            print(f"| ... and {len(report['staged_changes']) - 10} more staged files")
            print()
        
        print("+-" + "-" * 63 + "-+")
        print()
    
    # Merge Commits
    if report['merge_commits']:
        print("+-" + "-" * 63 + "-+")
        print("| [MERGE] Recent Merge Commits".ljust(63) + "|")
        print("+-" + "-" * 63 + "-+")
        
        for merge in report['merge_commits'][:5]:
            date = datetime.fromisoformat(merge['date']).strftime('%Y-%m-%d %H:%M')
            print(f"| [MERGE] {merge['hash']:<8} {merge['author']:<20} {date:<17}")
            print(f"|    {merge['message'][:50]}...")
            print(f"|    Merged: {', '.join(merge['parents'])}")
            print()
        
        print("+-" + "-" * 63 + "-+")
        print()
    
    # Hot Files
    if report['hot_files']:
        print("+-" + "-" * 63 + "-+")
        print("| [HOT] Hot Files (Most Changed)".ljust(63) + "|")
        print("+-" + "-" * 63 + "-+")
        
        for hot_file in report['hot_files'][:10]:
            last = hot_file['last_commit']
            if last:
                source_emoji = {'ai': '[AI]', 'user': '[USER]'}[last.get('source', 'user')]
                date = datetime.fromisoformat(last['date']).strftime('%Y-%m-%d %H:%M')
                print(f"| {source_emoji} {hot_file['file']:<40}")
                print(f"|    {hot_file['commit_count']} commits  Last: {last['hash']:<8} {date}")
                print()
            else:
                print(f"| [FILE] {hot_file['file']:<40}")
                print(f"|    {hot_file['commit_count']} commits")
                print()
        
        print("+-" + "-" * 63 + "-+")
        print()
    
    # Change Velocity
    velocity = report['velocity']
    print("+-" + "-" * 63 + "-+")
    print("| [VELOCITY] Change Velocity (Last 7 days)".ljust(63) + "|")
    print("+-" + "-" * 63 + "-+")
    print(f"| Total commits: {velocity['total_commits']:<48}")
    print(f"| Average per day: {velocity['average_per_day']:.1f}{' ' * 46}")
    print()
    
    if velocity['daily_counts']:
        print("| Daily breakdown:")
        for date, count in sorted(velocity['daily_counts'].items(), reverse=True)[:7]:
            print(f"|   {date:<15} {count:<3} commits")
        print()
    
    print("+-" + "-" * 63 + "-+")
