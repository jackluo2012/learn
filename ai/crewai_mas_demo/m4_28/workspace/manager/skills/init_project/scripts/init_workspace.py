#!/usr/bin/env python3

import os
import json
import argparse
from pathlib import Path

def create_directories(shared_dir):
    """Create required directories in the shared workspace."""
    dirs_to_create = ["needs/", "design/", "mailboxes/", "sop/"]
    created_dirs = []
    
    for dir_name in dirs_to_create:
        dir_path = os.path.join(shared_dir, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            created_dirs.append(dir_name)
    
    return created_dirs

def create_mailbox_files(shared_dir, roles):
    """Create mailbox JSON files for each role."""
    created_files = []
    skipped_files = []
    
    for role in roles:
        mailbox_path = os.path.join(shared_dir, f"mailboxes/{role}.json")
        if not os.path.exists(mailbox_path):
            # Create empty mailbox with read status
            with open(mailbox_path, 'w') as f:
                json.dump({"read": False}, f)
            created_files.append(f"mailboxes/{role}.json")
        else:
            skipped_files.append(f"mailboxes/{role}.json")
    
    return created_files, skipped_files

def create_workspace_rules(shared_dir, project_name):
    """Create WORKSPACE_RULES.md file."""
    rules_path = os.path.join(shared_dir, "WORKSPACE_RULES.md")
    created_files = []
    
    if not os.path.exists(rules_path):
        rules_content = f"""# {project_name} - Workspace Rules

## Directory Structure
- needs/: Requirements documentation
- design/: Design documents
- mailboxes/: Role-specific mailboxes
- sop/: Standard Operating Procedures

## Mailbox Usage
- Each role has a dedicated mailbox
- Messages are marked as read/unread
- Human role mailbox is used for human-AI interaction
"""
        with open(rules_path, 'w') as f:
            f.write(rules_content)
        created_files.append("WORKSPACE_RULES.md")
    
    return created_files

def main():
    parser = argparse.ArgumentParser(description='Initialize shared workspace')
    parser.add_argument('--shared-dir', required=True, help='Path to shared directory')
    parser.add_argument('--roles', nargs='+', required=True, help='List of roles')
    parser.add_argument('--project-name', required=True, help='Project name')
    
    args = parser.parse_args()
    
    # Ensure shared directory exists
    os.makedirs(args.shared_dir, exist_ok=True)
    
    # Create directories
    created_dirs = create_directories(args.shared_dir)
    
    # Create mailbox files
    created_mailboxes, skipped_mailboxes = create_mailbox_files(args.shared_dir, args.roles)
    
    # Create workspace rules
    created_rules = create_workspace_rules(args.shared_dir, args.project_name)
    
    # Prepare output
    result = {
        "errcode": 0,
        "data": {
            "created_dirs": created_dirs,
            "created_files": created_mailboxes + created_rules,
            "skipped_files": skipped_mailboxes
        }
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()