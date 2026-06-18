#!/usr/bin/env python3
import sys
import os
import json
import urllib.request
import urllib.error
import time
import argparse

def load_config():
    config_path = os.path.expanduser('~/.nowledge-mem/config.json')
    config = {
        'apiUrl': 'http://127.0.0.1:14242',
        'apiKey': ''
    }
    
    # 1. Config file
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'apiUrl' in data:
                    config['apiUrl'] = data['apiUrl'].rstrip('/')
                if 'apiKey' in data:
                    config['apiKey'] = data['apiKey']
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to load config from {config_path}: {e}\n")

    # 2. Env vars override
    env_url = os.environ.get('NMEM_API_URL')
    if env_url:
        config['apiUrl'] = env_url.rstrip('/')
    env_key = os.environ.get('NMEM_API_KEY')
    if env_key:
        config['apiKey'] = env_key

    return config

def make_request(config, path, method='GET', body=None):
    url = f"{config['apiUrl']}{path}"
    headers = {
        'Content-Type': 'application/json',
        'APP': 'Google Antigravity'
    }
    if config['apiKey']:
        headers['Authorization'] = f"Bearer {config['apiKey']}"

    data_bytes = None
    if body is not None:
        data_bytes = json.dumps(body).encode('utf-8')

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            res_body = res.read().decode('utf-8')
            return json.loads(res_body) if res_body else {}
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        try:
            err_data = json.loads(err_msg)
            message = err_data.get('detail', str(e))
        except Exception:
            message = err_msg or str(e)
        raise Exception(f"HTTP {e.code}: {message}")
    except Exception as e:
        raise Exception(f"Network error: {e}")

def get_skills_list(config):
    # Fetch all skills from nmem
    res = make_request(config, '/skills')
    skills = res.get('skills', [])
    # Filter to only show active, candidate, and archived skills
    allowed_stages = {'active', 'candidate', 'archived'}
    filtered = [s for s in skills if s.get('stage') in allowed_stages]
    return filtered

def list_command(config):
    try:
        skills = get_skills_list(config)
        if not skills:
            print("No skills available to install.")
            return
        
        print(f"{'ID':<20} | {'STAGE':<10} | {'TITLE'}")
        print("-" * 80)
        for s in skills:
            title = s.get('title') or s.get('headline') or s.get('id')
            print(f"{s['id']:<20} | {s['stage']:<10} | {title}")
    except Exception as e:
        sys.stderr.write(f"Error listing skills: {e}\n")
        sys.exit(1)

def suggest_command(config, workspace_root):
    if not os.path.exists(workspace_root):
        sys.stderr.write(f"Error: Workspace root '{workspace_root}' does not exist.\n")
        sys.exit(1)

    # Analyze files in workspace root
    makefile_exists = os.path.exists(os.path.join(workspace_root, 'Makefile'))
    gha_exists = os.path.exists(os.path.join(workspace_root, '.github', 'workflows'))
    git_exists = os.path.exists(os.path.join(workspace_root, '.git'))
    
    flatpak_exists = False
    aetherpak_exists = False
    for root, dirs, files in os.walk(workspace_root):
        if '.git' in dirs:
            dirs.remove('.git')
        for f in files:
            if f.endswith('.flatpak') or f.endswith('.flatpakrepo') or 'flatpak' in f.lower():
                flatpak_exists = True
            if 'aetherpak' in f.lower():
                aetherpak_exists = True

    suggestions = []

    try:
        skills = get_skills_list(config)
        for s in skills:
            sid = s.get('id', '')
            title = (s.get('title') or s.get('headline') or '').lower()
            desc = (s.get('description') or '').lower()
            
            relevance = 0
            reasons = []

            if "makefile" in title or "makefile" in desc:
                if makefile_exists:
                    relevance += 3
                    reasons.append("Makefile detected in workspace root")
            if "github actions" in title or "gha" in title or "github actions" in desc or "semver" in title:
                if gha_exists:
                    relevance += 3
                    reasons.append(".github/workflows directory detected")
            if "flatpak" in title or "flatpak" in desc:
                if flatpak_exists:
                    relevance += 3
                    reasons.append("Flatpak related files detected")
            if "aetherpak" in title or "aetherpak" in desc:
                if aetherpak_exists:
                    relevance += 4
                    reasons.append("AetherPak configuration or files detected")
            if "git" in title or "commit" in title or "git" in desc:
                if git_exists:
                    relevance += 2
                    reasons.append("Git repository detected")

            if relevance > 0:
                suggestions.append({
                    'skill': s,
                    'relevance': relevance,
                    'reasons': reasons
                })

        # Sort suggestions by relevance score descending
        suggestions.sort(key=lambda x: x['relevance'], reverse=True)

        if not suggestions:
            print("No matching skills suggested for this workspace based on file patterns.")
            return

        print("Suggested skills for this project:")
        print("-" * 80)
        for sug in suggestions:
            s = sug['skill']
            title = s.get('title') or s.get('headline') or s.get('id')
            reason_str = ", ".join(sug['reasons'])
            print(f"Skill: {title} ({s['id']}) [Stage: {s['stage']}]")
            print(f"  Reason: {reason_str}")
            print(f"  Description: {s.get('description') or s.get('pitch') or 'N/A'}")
            print()
    except Exception as e:
        sys.stderr.write(f"Error suggesting skills: {e}\n")
        sys.exit(1)

def install_command(config, skill_id, workspace_root, ignore_git):
    try:
        # 1. Fetch skill metadata to check stage
        print(f"Retrieving skill details for '{skill_id}'...")
        skill = make_request(config, f"/skills/{skill_id}")
        stage = skill.get('stage')
        
        if stage not in {'active', 'candidate', 'archived', 'draft'}:
            sys.stderr.write(f"Error: Skill '{skill_id}' is in stage '{stage}' which is not installable.\n")
            sys.exit(1)

        # 2. Compile if candidate
        if stage == 'candidate':
            print("Skill is in 'candidate' stage. Compiling skill...")
            compile_res = make_request(config, f"/agent/trigger/skill-compile?skill_id={skill_id}", method='POST')
            print(f"Compilation queued: {compile_res}")
            
            # Poll until compiled
            max_attempts = 12
            compiled = False
            for attempt in range(max_attempts):
                time.sleep(2)
                check = make_request(config, f"/skills/{skill_id}")
                if check.get('stage') == 'draft':
                    compiled = True
                    break
                print(f"Waiting for compilation (attempt {attempt+1}/{max_attempts})...")
            
            if not compiled:
                sys.stderr.write("Error: Skill compilation timed out.\n")
                sys.exit(1)
            print("Skill compiled successfully.")

        # 3. Fetch body using include_body=true
        print("Fetching skill markdown body...")
        skill_details = make_request(config, f"/skills/{skill_id}?include_body=true")
        body = skill_details.get('body')
        if not body:
            sys.stderr.write("Error: Skill body is empty or could not be generated.\n")
            sys.exit(1)

        # 4. Resolve folder name
        # Use name if available, otherwise clean title, fallback to skill_id
        clean_name = skill_details.get('name')
        if not clean_name:
            title = skill_details.get('title') or ""
            clean_name = "".join(c if c.isalnum() or c == '-' else '-' for c in title.lower())
            clean_name = "-".join(filter(None, clean_name.split('-')))
        if not clean_name:
            clean_name = skill_id

        # 5. Write file locally
        target_dir = os.path.join(workspace_root, '.agents', 'skills', clean_name)
        os.makedirs(target_dir, exist_ok=True)
        target_file = os.path.join(target_dir, 'SKILL.md')
        
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(body)
        print(f"Successfully installed/updated skill '{clean_name}' at:")
        print(f"  {target_file}")

        # 6. Git Exclude config
        if ignore_git:
            git_dir = os.path.join(workspace_root, '.git')
            if os.path.exists(git_dir):
                exclude_path = os.path.join(git_dir, 'info', 'exclude')
                os.makedirs(os.path.dirname(exclude_path), exist_ok=True)
                
                # Check if already excluded
                already_excluded = False
                exclude_line = f".agents/skills/{clean_name}/"
                if os.path.exists(exclude_path):
                    with open(exclude_path, 'r', encoding='utf-8') as ef:
                        lines = ef.read().splitlines()
                        if any(line.strip() == exclude_line for line in lines):
                            already_excluded = True

                if not already_excluded:
                    with open(exclude_path, 'a', encoding='utf-8') as ef:
                        ef.write(f"\n{exclude_line}\n")
                    print(f"Added local Git exclude for this skill at: {exclude_path}")
                else:
                    print(f"Skill is already excluded in {exclude_path}")
            else:
                print("Info: Workspace root is not a Git repository. Skipping Git exclude configuration.")
    except Exception as e:
        sys.stderr.write(f"Error during installation: {e}\n")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Nowledge Mem Skill Manager for Google Antigravity")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # List
    subparsers.add_parser('list', help="List all available skills from Nowledge Mem")

    # Suggest
    suggest_parser = subparsers.add_parser('suggest', help="Analyze workspace files and suggest relevant skills")
    suggest_parser.add_argument('workspace_root', help="Path to workspace root directory")

    # Install
    install_parser = subparsers.add_parser('install', help="Install or update a skill locally in the workspace")
    install_parser.add_argument('skill_id', help="ID of the skill to install")
    install_parser.add_argument('workspace_root', help="Path to workspace root directory")
    install_parser.add_argument('--ignore', action='store_true', help="Ignore the installed skill locally in Git (via .git/info/exclude)")

    args = parser.parse_args()
    config = load_config()

    if args.command == 'list':
        list_command(config)
    elif args.command == 'suggest':
        suggest_command(config, args.workspace_root)
    elif args.command == 'install':
        install_command(config, args.skill_id, args.workspace_root, args.ignore)

if __name__ == '__main__':
    main()
