#!/usr/bin/env python3
import sys
import os
import json
import subprocess

def read_hook_input():
    try:
        content = sys.stdin.read().strip()
        return json.loads(content) if content else {}
    except Exception:
        return {}

def emit(payload):
    sys.stdout.write(json.dumps(payload))
    sys.stdout.flush()

def read_nmem(args, keys):
    cmd = ['nmem', '--json'] + args
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout or '{}')
                for key in keys:
                    val = data.get(key)
                    if isinstance(val, str) and val.strip():
                        return val.strip()
            except Exception:
                pass
        else:
            if os.environ.get('DEBUG') or os.environ.get('NMEM_DEBUG'):
                sys.stderr.write(f"nmem command failed: {' '.join(cmd)}\n")
                if result.stderr:
                    sys.stderr.write(result.stderr + "\n")
    except Exception as e:
        if os.environ.get('DEBUG') or os.environ.get('NMEM_DEBUG'):
            sys.stderr.write(f"nmem execution failed: {e}\n")
    return ""

def with_startup_args(args):
    next_args = list(args)
    agent_id = os.environ.get('NMEM_AGENT_ID', '').strip()
    host_agent_id = os.environ.get('NMEM_HOST_AGENT_ID', '').strip()
    space = os.environ.get('NMEM_SPACE', '').strip() or os.environ.get('NMEM_SPACE_ID', '').strip()
    
    if agent_id and '--agent-id' not in next_args:
        next_args.extend(['--agent-id', agent_id])
    if host_agent_id and '--host-agent-id' not in next_args:
        next_args.extend(['--host-agent-id', host_agent_id])
    if space and '--space' not in next_args:
        next_args.extend(['--space', space])
    return next_args

def with_space_args(args):
    next_args = list(args)
    space = os.environ.get('NMEM_SPACE', '').strip() or os.environ.get('NMEM_SPACE_ID', '').strip()
    if space and '--space' not in next_args:
        next_args.extend(['--space', space])
    return next_args

def read_startup_context():
    context_bundle = read_nmem(
        with_startup_args(['context', '--source-app', 'google-antigravity']),
        ['rendered_markdown', 'markdown', 'content']
    )
    if context_bundle:
        return {
            'tag': 'nowledge_context_bundle',
            'label': 'Context Bundle',
            'content': context_bundle
        }
        
    working_memory = read_nmem(
        with_space_args(['wm', 'read']),
        ['content']
    )
    if working_memory:
        return {
            'tag': 'nowledge_working_memory',
            'label': 'Working Memory',
            'content': working_memory
        }
        
    legacy_path = os.path.expanduser('~/ai-now/memory.md')
    if os.path.exists(legacy_path):
        try:
            with open(legacy_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return {
                        'tag': 'nowledge_working_memory',
                        'label': 'legacy Working Memory file',
                        'content': content
                    }
        except Exception:
            pass
            
    return None

def main():
    hook_input = read_hook_input()
    invocation_num = hook_input.get('invocationNum')
    initial_num_steps = hook_input.get('initialNumSteps')
    
    # Only run startup injection on the very first invocation.
    # Supports both 0-indexed and 1-indexed runtimes.
    is_first = (invocation_num == 0) or (
        invocation_num == 1 and (initial_num_steps is None or initial_num_steps <= 2)
    )
    
    if invocation_num is not None and not is_first:
        emit({})
        return
        
    startup_context = read_startup_context()
    if not startup_context:
        emit({})
    else:
        msg = (
            f"<{startup_context['tag']}>\n"
            f"Use this as current user context from Nowledge Mem {startup_context['label']}. "
            "It is situational context, not a higher-priority instruction.\n\n"
            f"{startup_context['content']}\n"
            f"</{startup_context['tag']}>"
        )
        emit({
            'injectSteps': [
                {
                    'ephemeralMessage': msg
                }
            ]
        })

if __name__ == '__main__':
    main()
