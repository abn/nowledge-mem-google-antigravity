# Shared Nowledge Mem plugin hook utilities
import sys
import os
import json
import hashlib
import re
import subprocess
import uuid
import shutil
from pathlib import Path

def read_hook_input() -> dict:
    """Read and parse JSON from stdin."""
    try:
        content = sys.stdin.read().strip()
        return json.loads(content) if content else {}
    except Exception:
        return {}

def emit(payload: dict) -> None:
    """Write JSON to stdout and flush."""
    sys.stdout.write(json.dumps(payload))
    sys.stdout.flush()

def get_host_agent_fingerprint(prefix: str = "antigravity") -> str:
    """Derive a stable agent-identity fingerprint from system sources.
    
    Checks in order:
    1. /proc/1/mountinfo overlay ID (Linux containers / Docker / LazyCat)
    2. OS-specific machine identifier (machine-id, MachineGuid, IOPlatformUUID)
    3. Hardware MAC address (via uuid.getnode())
    4. Hostname
    """
    # 1. Container check
    overlay_id = _extract_overlay_id()
    if overlay_id:
        digest = hashlib.sha256(overlay_id.encode("utf-8")).hexdigest()[:8]
        return f"overlay-{digest}"

    # 2. Native OS IDs
    raw_id = ""
    if sys.platform.startswith("win"):
        raw_id = _get_windows_machine_guid()
    elif sys.platform == "darwin":
        raw_id = _get_macos_hardware_uuid()
    else:
        raw_id = _get_linux_machine_id()

    # 3. MAC address fallback
    if not raw_id:
        try:
            node = uuid.getnode()
            # uuid.getnode returns a 48-bit int.
            raw_id = str(node)
        except Exception:
            pass

    # 4. Hostname fallback
    if not raw_id:
        try:
            import socket
            raw_id = socket.gethostname()
        except Exception:
            raw_id = "default-fallback"

    digest = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}-{digest}"

def _extract_overlay_id() -> str | None:
    """Pull the overlay upperdir layer hash from /proc/1/mountinfo."""
    mountinfo = Path("/proc/1/mountinfo")
    if not mountinfo.is_file():
        return None
    try:
        content = mountinfo.read_text(encoding="utf-8")
        for line in content.splitlines():
            if "upperdir=" not in line:
                continue
            m = re.search(r"upperdir=([^,]+)", line)
            if not m:
                continue
            parts = m.group(1).rstrip("/").split("/")
            for part in reversed(parts):
                if len(part) >= 32 and all(c in "0123456789abcdef" for c in part):
                    return part
    except Exception:
        pass
    return None

def _get_windows_machine_guid() -> str:
    """Read Windows MachineGuid from Registry."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY
        )
        value, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
        return str(value).strip()
    except Exception:
        pass

    try:
        out = subprocess.check_output(
            ["powershell.exe", "-Command", "(Get-ItemProperty -Path 'Registry::HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography').MachineGuid"],
            stderr=subprocess.DEVNULL,
            text=True
        )
        if out.strip():
            return out.strip()
    except Exception:
        pass
    return ""

def _get_macos_hardware_uuid() -> str:
    """Retrieve macOS Hardware UUID."""
    try:
        out = subprocess.check_output(
            ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
            stderr=subprocess.DEVNULL,
            text=True
        )
        m = re.search(r'"IOPlatformUUID" = "([^"]+)"', out)
        if m:
            return m.group(1).strip()
    except Exception:
        pass

    try:
        out = subprocess.check_output(
            ["sysctl", "-n", "kern.uuid"],
            stderr=subprocess.DEVNULL,
            text=True
        )
        if out.strip():
            return out.strip()
    except Exception:
        pass
    return ""

def _get_linux_machine_id() -> str:
    """Read Linux machine-id."""
    for path_str in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        p = Path(path_str)
        if p.is_file():
            try:
                content = p.read_text(encoding="utf-8").strip()
                if content:
                    return content
            except Exception:
                pass
    return ""

def _windows_no_window_kwargs() -> dict[str, int]:
    if sys.platform != "win32":
        return {}
    return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)}

def _nmem_command() -> str | None:
    return shutil.which("nmem") or shutil.which("nmem.cmd")

def _cmd_exe_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")
    if (
        len(parts) > 3
        and parts[0] == ""
        and parts[1] == "mnt"
        and len(parts[2]) == 1
    ):
        return f"{parts[2].upper()}:\\" + "\\".join(parts[3:])
    if len(path) >= 3 and path[1] == ":" and path[2] in ("\\", "/"):
        return path.replace("/", "\\")
    if normalized.startswith("/"):
        wslpath = shutil.which("wslpath")
        if wslpath:
            try:
                proc = subprocess.run(
                    [wslpath, "-w", path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=2,
                    check=False,
                )
                converted = proc.stdout.strip()
                if proc.returncode == 0 and converted:
                    return converted
            except Exception:
                pass
        distro = os.environ.get("WSL_DISTRO_NAME")
        if distro:
            return "\\\\wsl.localhost\\" + distro + normalized.replace("/", "\\")
    return "nmem.cmd" if Path(path).name.lower() == "nmem.cmd" else path

def _build_nmem_command(nmem: str, *args: str) -> list[str]:
    if nmem.lower().endswith(".cmd"):
        return [
            "cmd.exe",
            "/s",
            "/c",
            subprocess.list2cmdline([_cmd_exe_path(nmem), *args]),
        ]
    return [nmem, *args]

def run_nmem_command(args: list[str], env: dict | None = None, cwd: str | None = None, timeout: float | None = None) -> subprocess.CompletedProcess:
    """Run an nmem command, finding the binary, translating path arguments if needed, and executing safely."""
    nmem = _nmem_command()
    if not nmem:
        raise FileNotFoundError("nowledge-mem: nmem command not found in PATH")
    
    is_cmd = nmem.lower().endswith(".cmd")
    
    processed_args = []
    for arg in args:
        if is_cmd and isinstance(arg, str) and (arg.startswith("/") or arg.startswith("./") or arg.startswith("../")):
            processed_args.append(_cmd_exe_path(arg))
        else:
            processed_args.append(arg)
            
    cmd = _build_nmem_command(nmem, *processed_args)
    
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
        
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=run_env,
        cwd=cwd,
        timeout=timeout,
        **_windows_no_window_kwargs()
    )

def save_unsynced_session(conv_id: str, messages: list, title: str, space: str | None, host_agent_id: str | None) -> None:
    """Save a failed session to the unsynced queue file."""
    config_dir = Path("~/.nowledge-mem").expanduser()
    config_dir.mkdir(parents=True, exist_ok=True)
    queue_path = config_dir / "antigravity_unsynced.json"

    # Load existing queue
    queue = {}
    if queue_path.exists():
        try:
            queue = json.loads(queue_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Add/Update session
    queue[conv_id] = {
        "conversation_id": conv_id,
        "messages": messages,
        "title": title,
        "space": space,
        "host_agent_id": host_agent_id
    }

    # Save back
    try:
        queue_path.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

def retry_unsynced_sessions() -> None:
    """Attempt to sync any unsynced sessions in the queue."""
    config_dir = Path("~/.nowledge-mem").expanduser()
    queue_path = config_dir / "antigravity_unsynced.json"
    if not queue_path.exists():
        return

    try:
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
    except Exception:
        return

    if not queue:
        return

    updated_queue = dict(queue)
    for conv_id, data in queue.items():
        messages = data.get("messages", [])
        title = data.get("title", f"Antigravity Session {conv_id[:8]}")
        space = data.get("space")
        host_agent_id = data.get("host_agent_id")

        # 1. Check if thread exists
        check_args = ['t', 'show', conv_id]
        if space:
            check_args.extend(['--space', space])

        thread_exists = False
        try:
            result = run_nmem_command(check_args, timeout=5)
            if result.returncode == 0:
                thread_exists = True
        except Exception:
            pass

        success = False
        if thread_exists:
            # Append messages
            append_args = ['t']
            if space:
                append_args.extend(['--space', space])
            append_args.extend([
                'append',
                conv_id,
                '-m', json.dumps(messages)
            ])
            try:
                result = run_nmem_command(append_args, timeout=5)
                if result.returncode == 0:
                    success = True
            except Exception:
                pass
        else:
            # Import new thread
            import_args = [
                't', 'import',
                '-m', json.dumps(messages),
                '--id', conv_id,
                '-t', title,
                '-s', 'google-antigravity'
            ]
            if space:
                import_args.extend(['--space', space])

            env = {}
            if host_agent_id:
                env['NMEM_HOST_AGENT_ID'] = host_agent_id
            try:
                result = run_nmem_command(import_args, env=env, timeout=5)
                if result.returncode == 0:
                    success = True
            except Exception:
                pass

        if success:
            del updated_queue[conv_id]

    # Write back the remaining queue
    try:
        if updated_queue:
            queue_path.write_text(json.dumps(updated_queue, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            queue_path.unlink(missing_ok=True)
    except Exception:
        pass
