"""
Bash Tool — Secure command execution (Path Sandbox)
"""
import os
import re
import shlex
import subprocess
from pathlib import Path

from config import (
    BANNED_COMMANDS, DANGEROUS_PATTERNS,
    ALLOWED_DIRS, BASH_TIMEOUT, BASH_MAX_OUTPUT,
)


def _is_within_dir(path: str, base_dir: str) -> bool:
    """Robust containment check that avoids startswith path-bypass issues."""
    try:
        path_norm = os.path.normcase(os.path.realpath(path))
        base_norm = os.path.normcase(os.path.realpath(os.path.expanduser(base_dir)))
        return os.path.commonpath([path_norm, base_norm]) == base_norm
    except Exception:
        return False


def validate_command(command: str) -> tuple[bool, str]:
    """
    Runs the command through security filters.
    Returns: (is_valid, message)
    """
    command_lower = command.lower()

    for banned in BANNED_COMMANDS:
        banned_lower = banned.lower()
        if len(banned_lower) <= 2 or " " not in banned_lower:
            if re.search(r'\b' + re.escape(banned_lower) + r'\b', command_lower):
                return False, f"❌ SECURITY: '{banned}' command is banned!"

    for pattern in DANGEROUS_PATTERNS:
        if pattern in command_lower:
            return False, f"❌ SECURITY: Dangerous pattern detected: '{pattern}'"

    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()

    def _is_abs_path_arg(arg: str) -> bool:
        return (
            arg.startswith("/")
            or arg.startswith("~")
            or bool(re.match(r"^[a-zA-Z]:[\\/]", arg))
            or arg.startswith("\\\\")
        )

    for arg in parts[1:]:
        if _is_abs_path_arg(arg):
            real_path = os.path.realpath(os.path.expanduser(arg))
            if not any(_is_within_dir(real_path, allowed) for allowed in ALLOWED_DIRS):
                home = str(Path.home())
                if not _is_within_dir(real_path, home) and not _is_within_dir(real_path, "/tmp"):
                    return False, f"❌ SECURITY: '{arg}' is not in allowed directories!"

    return True, "✅"


def bash(command: str) -> str:
    """
    Run a secure bash command.
    - Banned commands are blocked
    - Dangerous patterns are blocked
    - Path sandbox check is enforced
    - Output limited to BASH_MAX_OUTPUT characters
    """
    valid, msg = validate_command(command)
    if not valid:
        return msg

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=BASH_TIMEOUT,
            cwd=str(Path.home()),
        )

        output = result.stdout if result.stdout else result.stderr

        if len(output) > BASH_MAX_OUTPUT:
            from core.llm import summarize_output
            output = summarize_output(output)

        if result.returncode == 0:
            return f"✅ Command successful:\n{output}"
        else:
            return f"⚠️ Command returned error (exit code: {result.returncode}):\n{output}"

    except subprocess.TimeoutExpired:
        return f"❌ TIMEOUT: Command {BASH_TIMEOUT} seconds! (TIMEOUT)"

    except Exception as e:
        return f"❌ ERROR: {type(e).__name__}: {str(e)}"
