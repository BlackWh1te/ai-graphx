# Git hooks and commit tracking for graphx
import subprocess
import json
from pathlib import Path
from datetime import datetime, timezone
import os
import git

def detect_commit_source(repo_path, commit_hash):
    """Detect if commit was made by AI or user."""
    try:
        repo = git.Repo(repo_path)
        commit = repo.commit(commit_hash)
    except:
        return 'user'
    
    # Check commit message for AI signatures
    message = commit.message.lower()
    ai_signatures = [
        'co-authored-by: claude',
        'co-authored-by: copilot',
        'automated commit',
        'auto-generated',
        'bot commit',
        'github-actions[bot]',
        'dependabot[bot]',
        'renovate[bot]',
    ]
    
    if any(sig in message for sig in ai_signatures):
        return 'ai'
    
    # Check author email for AI patterns
    email = commit.author.email.lower() if commit.author.email else ''
    if any(ai in email for ai in ['bot', 'ai', 'automated', 'noreply', 'github-actions']):
        return 'ai'
    
    # Check if author is a known AI tool
    known_ai_authors = ['github-actions[bot]', 'claude-ai', 'copilot', 'dependabot', 'renovate']
    if commit.author.name in known_ai_authors:
        return 'ai'
    
    return 'user'

def capture_commit(repo_path):
    """Capture commit metadata and store in commits.json."""
    try:
        repo = git.Repo(repo_path)
        commit = repo.head.commit
    except:
        return None
    
    # Get changed files in this commit
    files_changed = []
    
    try:
        if commit.parents:
            diff = commit.diff(commit.parents[0])
        else:
            # First commit - show all files
            diff = [item for item in commit.tree.traverse() if item.type == 'blob']
        
        for change in diff if hasattr(diff, '__iter__') else []:
            try:
                file_path = change.a_path if hasattr(change, 'a_path') and change.a_path else change.b_path
                if not file_path:
                    continue
                    
                action = 'modified'
                if hasattr(change, 'new_file') and change.new_file:
                    action = 'added'
                elif hasattr(change, 'deleted_file') and change.deleted_file:
                    action = 'deleted'
                
                # Get file size
                full_path = Path(repo_path) / file_path
                file_size = full_path.stat().st_size if full_path.exists() else 0
                
                files_changed.append({
                    'file': file_path,
                    'action': action,
                    'size': file_size
                })
            except:
                continue
    except:
        # Fallback: get files from tree
        try:
            for item in commit.tree.traverse():
                if item.type == 'blob':
                    files_changed.append({
                        'file': item.path,
                        'action': 'added',
                        'size': 0
                    })
        except:
            pass
    
    # Detect source
    source = detect_commit_source(repo_path, commit.hexsha)
    
    # Get branch name
    try:
        branch = repo.active_branch.name
    except:
        try:
            branch = repo.head.reference.name
        except:
            branch = 'detached'
    
    # Detect if merge commit
    is_merge = len(commit.parents) > 1
    
    commit_data = {
        'hash': commit.hexsha[:7],  # Short hash
        'full_hash': commit.hexsha,
        'author': commit.author.name,
        'email': commit.author.email,
        'date': commit.committed_datetime.isoformat(),
        'message': commit.message.strip(),
        'source': source,
        'files_changed': files_changed,
        'branch': branch,
        'is_merge': is_merge,
        'parents': [p.hexsha[:7] for p in commit.parents] if commit.parents else []
    }
    
    # Store in commits.json
    commits_file = Path(repo_path) / 'graphx-out' / 'commits.json'
    commits_file.parent.mkdir(parents=True, exist_ok=True)
    
    if commits_file.exists():
        try:
            data = json.loads(commits_file.read_text())
        except:
            data = {'commits': []}
    else:
        data = {'commits': []}
    
    # Avoid duplicates
    if not any(c['hash'] == commit_data['hash'] for c in data['commits']):
        data['commits'].insert(0, commit_data)  # Add to front
        commits_file.write_text(json.dumps(data, indent=2))
    
    return commit_data

def install_commit_hook(repo_path):
    """Install the post-commit hook."""
    hooks_dir = Path(repo_path) / '.git' / 'hooks'
    hooks_dir.mkdir(parents=True, exist_ok=True)
    
    hook_file = hooks_dir / 'post-commit'
    
    # Check if hook already exists and append to it
    if hook_file.exists():
        content = hook_file.read_text()
        if 'graphx capture-commit' not in content:
            # Append our hook
            hook_file.write_text(content + '\n# GraphX commit tracking\npython3 -m graphx capture-commit\n')
            print('[graphx] Appended to existing post-commit hook')
        else:
            print('[graphx] Hook already installed')
    else:
        # Create new hook
        hook_script = """#!/bin/bash
# GraphX post-commit hook - capture commit metadata
python3 -m graphx capture-commit
"""
        hook_file.write_text(hook_script)
        hook_file.chmod(0o755)
        print('[graphx] Installed new post-commit hook')

def uninstall_commit_hook(repo_path):
    """Remove the post-commit hook."""
    hook_file = Path(repo_path) / '.git' / 'hooks' / 'post-commit'
    
    if hook_file.exists():
        content = hook_file.read_text()
        if 'graphx capture-commit' in content:
            # Remove our hook lines
            lines = [line for line in content.split('\n') 
                    if 'graphx capture-commit' not in line 
                    and not (line.strip().startswith('# GraphX') and 'commit tracking' in line)]
            hook_file.write_text('\n'.join(lines))
            print('[graphx] Removed graphx hook from post-commit')
        else:
            print('[graphx] No graphx hook found in post-commit')
    else:
        print('[graphx] No post-commit hook found')

def check_hook_status(repo_path):
    """Check if hook is installed."""
    hook_file = Path(repo_path) / '.git' / 'hooks' / 'post-commit'
    
    if not hook_file.exists():
        return 'not_installed'
    
    content = hook_file.read_text()
    if 'graphx capture-commit' in content:
        return 'installed'
    
    return 'other_hook'
