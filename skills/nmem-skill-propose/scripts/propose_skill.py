#!/usr/bin/env python3
import sys
import os
import json
import urllib.request
import urllib.error

def load_config():
    config_path = os.path.expanduser('~/.nowledge-mem/config.json')
    config = {
        'apiUrl': 'http://127.0.0.1:14242',
        'apiKey': ''
    }
    
    # 1. Load from config file
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

    # 2. Environment variables override
    env_url = os.environ.get('NMEM_API_URL')
    if env_url:
        config['apiUrl'] = env_url.rstrip('/')
    env_key = os.environ.get('NMEM_API_KEY')
    if env_key:
        config['apiKey'] = env_key

    return config

def get_endpoint_url(config, path):
    api_url = config['apiUrl'].rstrip('/')
    # Check if this is a local loopback connection
    is_loopback = any(x in api_url for x in ['127.0.0.1', 'localhost', '::1'])
    
    if not is_loopback and not api_url.endswith('/remote-api'):
        return f"{api_url}/remote-api{path}"
    else:
        return f"{api_url}{path}"

def main():
    if len(sys.argv) < 2:
        print("Usage: propose_skill.py <draft_md_file_path> [--force]")
        sys.exit(1)

    draft_path = sys.argv[1]
    force_import = "--force" in sys.argv or "-f" in sys.argv

    if not os.path.exists(draft_path):
        sys.stderr.write(f"Error: Draft file '{draft_path}' does not exist.\n")
        sys.exit(1)

    try:
        with open(draft_path, 'r', encoding='utf-8') as f:
            skill_md = f.read()
    except Exception as e:
        sys.stderr.write(f"Error: Failed to read '{draft_path}': {e}\n")
        sys.exit(1)

    # Basic frontmatter validation
    if not skill_md.strip().startswith('---'):
        sys.stderr.write("Warning: The draft file does not seem to start with frontmatter (---).\n")

    config = load_config()
    endpoint = "/agent/skill-builder/import"
    url = get_endpoint_url(config, endpoint)

    headers = {
        'Content-Type': 'application/json',
        'APP': 'Google Antigravity'
    }
    if config['apiKey']:
        headers['Authorization'] = f"Bearer {config['apiKey']}"
        headers['X-NMEM-API-Key'] = config['apiKey']

    payload = {
        'skill_md': skill_md,
        'force': force_import or True  # Default to True to allow overwriting/updating existing
    }
    data_bytes = json.dumps(payload).encode('utf-8')

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method='POST')

    print(f"Uploading skill to {url}...")
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            res_body = res.read().decode('utf-8')
            response_data = json.loads(res_body) if res_body else {}
            
            created = response_data.get('created', False)
            skill = response_data.get('skill', {})
            skill_id = skill.get('id', 'unknown')
            skill_name = skill.get('name', 'unknown')
            stage = skill.get('stage', 'unknown')

            print("\n" + "="*50)
            print("🟢 Skill Proposal Successfully Submitted!")
            print("="*50)
            print(f"Skill ID:    {skill_id}")
            print(f"Name:        {skill_name}")
            print(f"Stage:       {stage}")
            print(f"Status:      {'Created' if created else 'Updated'}")
            print("-"*50)
            print("To make this skill live to your AI tools, run:")
            print(f"  nmem skills activate -y {skill_id}")
            print("="*50 + "\n")
            
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        try:
            err_data = json.loads(err_msg)
            message = err_data.get('detail', str(e))
        except Exception:
            message = err_msg or str(e)
        sys.stderr.write(f"API Error (HTTP {e.code}): {message}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Connection Error: {e}\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
