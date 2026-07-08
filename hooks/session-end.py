#!/usr/bin/env python3
import sys
import os
import json
import re
import time
import subprocess
import uuid
import hashlib
from pathlib import Path

# Add the hooks directory to sys.path to allow importing nmem_shared
sys.path.insert(0, str(Path(__file__).parent.resolve()))
import nmem_shared

def main():
    hook_input = nmem_shared.read_hook_input()
    conversation_id = hook_input.get('conversationId')
    transcript_path = hook_input.get('transcriptPath')
    artifact_directory_path = hook_input.get('artifactDirectoryPath')
    
    if not conversation_id or not transcript_path:
        nmem_shared.emit({})
        return
        
    space = os.environ.get('NMEM_SPACE', '').strip() or os.environ.get('NMEM_SPACE_ID', '').strip()
    host_agent_id = os.environ.get('NMEM_HOST_AGENT_ID', '').strip()
    if not host_agent_id:
        host_agent_id = nmem_shared.get_host_agent_fingerprint()
    os.environ['NMEM_HOST_AGENT_ID'] = host_agent_id
    
    try:
        delays = (0.0, 0.5, 1.0)
        success = False
        messages = []
        title = f"Antigravity Session {conversation_id[:8]}"
        
        for delay in delays:
            if delay > 0:
                time.sleep(delay)
                
            if not os.path.exists(transcript_path):
                continue
                
            try:
                current_messages = []
                with open(transcript_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            step = json.loads(line)
                            source = step.get('source')
                            content = step.get('content')
                            step_type = step.get('type')
                            
                            if source == 'USER_EXPLICIT' and isinstance(content, str):
                                current_messages.append({
                                    'role': 'user',
                                    'content': content
                                })
                            elif source == 'MODEL' and step_type == 'PLANNER_RESPONSE' and isinstance(content, str):
                                current_messages.append({
                                    'role': 'assistant',
                                    'content': content
                                })
                        except Exception:
                            pass
                messages = current_messages
            except Exception:
                pass
                
            if not messages:
                continue
                
            # Generate clean title from first user request
            title = f"Antigravity Session {conversation_id[:8]}"
            first_user_msg = next((m for m in messages if m['role'] == 'user'), None)
            if first_user_msg and first_user_msg.get('content'):
                clean_text = first_user_msg['content']
                match = re.search(r'<USER_REQUEST>([\s\S]*?)</USER_REQUEST>', clean_text)
                if match:
                    clean_text = match.group(1)
                clean_text = ' '.join(clean_text.strip().split())
                if len(clean_text) > 60:
                    title = clean_text[:60] + "..."
                elif len(clean_text) > 0:
                    title = clean_text
                    
            # Check if the thread exists
            check_args = ['t', 'show', conversation_id]
            if space:
                check_args.extend(['--space', space])
                
            thread_exists = False
            try:
                result = nmem_shared.run_nmem_command(check_args, timeout=3)
                if result.returncode == 0:
                    thread_exists = True
            except Exception as e:
                if os.environ.get('DEBUG') or os.environ.get('NMEM_DEBUG'):
                    sys.stderr.write(f"nmem t show execution failed: {e}\n")
                    
            if thread_exists:
                # Append messages to existing thread
                append_args = ['t']
                if space:
                    append_args.extend(['--space', space])
                append_args.extend([
                    'append',
                    conversation_id,
                    '-m', json.dumps(messages)
                ])
                try:
                    result = nmem_shared.run_nmem_command(append_args, timeout=5)
                    if result.returncode == 0:
                        success = True
                        break
                    else:
                        if os.environ.get('DEBUG') or os.environ.get('NMEM_DEBUG'):
                            sys.stderr.write(f"nmem t append failed: {result.stderr}\n")
                except Exception as e:
                    if os.environ.get('DEBUG') or os.environ.get('NMEM_DEBUG'):
                        sys.stderr.write(f"nmem t append execution failed: {e}\n")
            else:
                # Import new thread
                import_args = [
                    't', 'import',
                    '-m', json.dumps(messages),
                    '--id', conversation_id,
                    '-t', title,
                    '-s', 'google-antigravity'
                ]
                if space:
                    import_args.extend(['--space', space])
                    
                try:
                    result = nmem_shared.run_nmem_command(import_args, timeout=5)
                    if result.returncode == 0:
                        success = True
                        break
                    else:
                        if os.environ.get('DEBUG') or os.environ.get('NMEM_DEBUG'):
                            sys.stderr.write(f"nmem t import failed: {result.stderr}\n")
                except Exception as e:
                    if os.environ.get('DEBUG') or os.environ.get('NMEM_DEBUG'):
                        sys.stderr.write(f"nmem t import execution failed: {e}\n")
                        
        if not success and messages:
            nmem_shared.save_unsynced_session(conversation_id, messages, title, space, host_agent_id)
            
        # Seamlessly capture /learn learnings to nmem
        try:
            nmem_shared.sync_learnings_if_any(conversation_id, transcript_path, artifact_directory_path, space)
        except Exception as e:
            if os.environ.get('DEBUG') or os.environ.get('NMEM_DEBUG'):
                sys.stderr.write(f"Learning sync failed: {e}\n")
            
    except Exception as e:
        if os.environ.get('DEBUG') or os.environ.get('NMEM_DEBUG'):
            sys.stderr.write(f"Hook execution failed: {e}\n")
            
    nmem_shared.emit({})

if __name__ == '__main__':
    main()
