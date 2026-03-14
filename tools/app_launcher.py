"""
App Launcher — Async app launch via Hyprland
  Uses hyprctl dispatch exec; does not block the Python event loop.
"""
import json
import os
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path


IS_WINDOWS = os.name == "nt"


def _hyprland_available() -> bool:
    return shutil.which("hyprctl") is not None


def _run_windows_start(target: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["cmd", "/c", "start", "", target],
            timeout=8,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False, "❌ cmd.exe not found."
    except subprocess.TimeoutExpired:
        return False, "❌ Windows start command timed out."

    if result.returncode != 0:
        err = (result.stderr or result.stdout or "unknown error").strip()
        return False, f"❌ Windows start command failed: {err}"

    return True, ""


def _run_windows_powershell(script: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            timeout=10,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False, "❌ powershell not found."
    except subprocess.TimeoutExpired:
        return False, "❌ PowerShell command timed out."

    if result.returncode != 0:
        err = (result.stderr or result.stdout or "unknown error").strip()
        return False, f"❌ PowerShell command failed: {err}"

    return True, (result.stdout or "").strip()


def _hyprland_dispatch(*args: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["hyprctl", "dispatch", *args],
            timeout=5,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False, "❌ hyprctl not found. Is Hyprland running?"
    except subprocess.TimeoutExpired:
        return False, "❌ hyprctl timed out."

    if result.returncode != 0:
        error_text = (result.stderr or result.stdout or "unknown error").strip()
        return False, f"❌ Hyprland command failed: {error_text}"

    return True, ""


def _hyprland_json(*args: str) -> tuple[bool, object | str]:
    try:
        result = subprocess.run(
            ["hyprctl", *args, "-j"],
            timeout=5,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False, "❌ hyprctl not found. Is Hyprland running?"
    except subprocess.TimeoutExpired:
        return False, "❌ hyprctl timed out."

    if result.returncode != 0:
        error_text = (result.stderr or result.stdout or "unknown error").strip()
        return False, f"❌ Hyprland JSON command failed: {error_text}"

    try:
        return True, json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return False, f"❌ Hyprland JSON output could not be parsed: {exc}"


def _hyprland_exec(command: str) -> tuple[bool, str]:
    return _hyprland_dispatch("exec", command)


def _get_open_windows() -> tuple[bool, list[dict] | str]:
    ok, payload = _hyprland_json("clients")
    if not ok:
        return False, str(payload)
    if not isinstance(payload, list):
        return False, "❌ Hyprland clients output is not in expected format."
    return True, payload


def open_app(app_name: str) -> str:
    raw_name = (app_name or "").strip()
    if not raw_name:
        return "❌ Invalid application name."

    if IS_WINDOWS:
        ok, error = _run_windows_start(raw_name)
        if not ok:
            return error
        return f"✅ '{raw_name}' application started on Windows."

    clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "", raw_name)
    if not clean_name:
        return "❌ Invalid application name."

    if not _hyprland_available():
        try:
            subprocess.Popen([clean_name])
            return f"✅ '{clean_name}' application started."
        except Exception as exc:
            return f"❌ Could not start application '{clean_name}': {type(exc).__name__}: {exc}"

    ok, error = _hyprland_exec(clean_name)
    if not ok:
        return error

    return f"✅ '{clean_name}' application started via Hyprland."


def vscode_open_project(project_path: str) -> str:
    path_str = (project_path or "").strip().strip("\"'")
    if not path_str:
        return "❌ Project path cannot be empty."

    path_obj = Path(path_str).expanduser()
    if not path_obj.is_absolute():
        path_obj = Path.home() / path_obj

    try:
        resolved = path_obj.resolve(strict=False)
    except Exception:
        resolved = path_obj

    if not resolved.exists():
        return f"❌ Path not found: {resolved}"
    if not resolved.is_dir():
        return f"❌ A folder path must be provided to open in VS Code: {resolved}"

    if shutil.which("code") is not None:
        try:
            result = subprocess.run(
                ["code", str(resolved)],
                timeout=10,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return f"✅ VS Code opened: {resolved}"
        except Exception:
            pass

    if IS_WINDOWS:
        ok, error = _run_windows_start(str(resolved))
        if not ok:
            return "❌ VS Code CLI ('code') is not available. Install VS Code and enable the 'code' command."
        return f"✅ Opened folder on Windows: {resolved}"

    if not _hyprland_available():
        return "❌ VS Code CLI ('code') is not available. Install VS Code and enable the 'code' command."

    safe_path = str(resolved).replace("'", "'\\''")
    ok, error = _hyprland_exec(f"code '{safe_path}'")
    if not ok:
        return error

    return f"✅ VS Code opened: {resolved}"


def open_app_workspace(app_name: str, workspace_no: str | int) -> str:
    if IS_WINDOWS:
        result = open_app(app_name)
        if result.startswith("❌"):
            return result
        return result + "\nℹ️ Workspace placement is not supported on Windows; opened normally."

    if not _hyprland_available():
        result = open_app(app_name)
        if result.startswith("❌"):
            return result
        return result + "\nℹ️ Workspace placement requires Hyprland and was skipped."

    clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "", app_name)
    if not clean_name:
        return "❌ Invalid application name."

    value = str(workspace_no).strip()
    if not value:
        return "❌ Workspace number cannot be empty."

    if value == "0":
        target_ws = 10
    else:
        if not value.isdigit():
            return "❌ Workspace number must be between 1 and 10."
        target_ws = int(value)

    if target_ws < 1 or target_ws > 10:
        return "❌ Workspace number must be between 1 and 10."

    command = f"[workspace {target_ws}] {clean_name}"
    ok, error = _hyprland_exec(command)
    if not ok:
        return error

    return f"✅ '{clean_name}' launched on workspace {target_ws}."


def switch_workspace(workspace_no: str | int) -> str:
    if IS_WINDOWS:
        return "❌ Workspace switching is not supported on Windows by this adapter."

    if not _hyprland_available():
        return "❌ Workspace switching requires Hyprland and is not available on this platform."

    value = str(workspace_no).strip()
    if not value:
        return "❌ Workspace number cannot be empty."

    if value == "0":
        target_ws = 10
    else:
        if not value.isdigit():
            return "❌ Workspace number must be between 1 and 10."
        target_ws = int(value)

    if target_ws < 1 or target_ws > 10:
        return "❌ Workspace number must be between 1 and 10."

    ok, error = _hyprland_dispatch("workspace", str(target_ws))
    if not ok:
        return error

    return f"✅ Hyprland workspace {target_ws} activated."


def read_active_workspace() -> str:
    if IS_WINDOWS:
        return "❌ Active workspace query is not supported on Windows by this adapter."

    if not _hyprland_available():
        return "❌ Active workspace query requires Hyprland and is not available on this platform."

    ok, payload = _hyprland_json("activeworkspace")
    if not ok:
        return str(payload)

    assert isinstance(payload, dict)
    workspace_id = payload.get("id")
    workspace_name = payload.get("name") or workspace_id
    windows = payload.get("windows", 0)

    return (
        f"✅ Active workspace: {workspace_name}\n"
        f"ID: {workspace_id}\n"
        f"Open windows: {windows}"
    )


def list_open_windows() -> str:
    if IS_WINDOWS:
        script = (
            "Get-Process | "
            "Where-Object { $_.MainWindowTitle -and $_.MainWindowTitle.Trim().Length -gt 0 } | "
            "Select-Object -First 50 ProcessName,MainWindowTitle,Id | ConvertTo-Json"
        )
        ok, output = _run_windows_powershell(script)
        if not ok:
            return output
        if not output:
            return "❌ No open windows found."
        try:
            data = json.loads(output)
        except Exception as exc:
            return f"❌ Could not parse window list output: {type(exc).__name__}: {exc}"

        items = data if isinstance(data, list) else [data]
        if not items:
            return "❌ No open windows found."

        lines = [f"✅ Total open windows: {len(items)}", ""]
        for idx, item in enumerate(items, start=1):
            proc = str(item.get("ProcessName") or "-").strip()
            title = str(item.get("MainWindowTitle") or "-").strip()
            pid = str(item.get("Id") or "?").strip()
            lines.append(f"{idx}. [{pid}] {proc} | {title}")
        return "\n".join(lines)

    if not _hyprland_available():
        return "❌ Open window listing requires Hyprland and is not available on this platform."

    ok, payload = _get_open_windows()
    if not ok:
        return str(payload)

    clients = payload
    if not clients:
        return "❌ No open windows found."

    lines = [f"✅ Total open windows: {len(clients)}", ""]
    for index, client in enumerate(clients, start=1):
        klass = str(client.get("class") or "-").strip()
        title = str(client.get("title") or "-").strip()
        ws = client.get("workspace") or {}
        ws_id = ws.get("id", "?") if isinstance(ws, dict) else "?"
        lines.append(f"{index}. [{ws_id}] {klass} | {title}")

    return "\n".join(lines)


def move_window_workspace(window: str, workspace_no: str | int) -> str:
    if IS_WINDOWS:
        return "❌ Moving windows between workspaces is not supported on Windows by this adapter."

    if not _hyprland_available():
        return "❌ Moving windows between workspaces requires Hyprland and is not available on this platform."

    target_window = window.strip().lower()
    if not target_window:
        return "❌ Window name cannot be empty."

    target_norm = re.sub(r"[^a-z0-9]", "", target_window)
    aliases = {target_window, target_norm}
    if target_norm in {"vscode", "visualstudiocode", "code"}:
        aliases.update({"vscode", "vs code", "visual studio code", "code"})
    elif target_norm in {"firefox", "mozilla"}:
        aliases.update({"firefox", "mozilla"})
    elif target_norm in {"chrome", "googlechrome", "chromium"}:
        aliases.update({"chrome", "google chrome", "chromium"})
    elif target_norm in {"terminal", "kitty", "alacritty", "konsole"}:
        aliases.update({"terminal", "kitty", "alacritty", "konsole"})

    value = str(workspace_no).strip()
    if not value:
        return "❌ Workspace number cannot be empty."

    if value == "0":
        target_workspace = 10
    else:
        if not value.isdigit():
            return "❌ Workspace number must be between 1 and 10."
        target_workspace = int(value)

    if target_workspace < 1 or target_workspace > 10:
        return "❌ Workspace number must be between 1 and 10."

    ok, payload = _get_open_windows()
    if not ok:
        return str(payload)

    clients = payload
    if not clients:
        return "❌ No open windows found."

    def _score(client: dict) -> int:
        fields = [
            str(client.get("title") or "").lower(),
            str(client.get("initialTitle") or "").lower(),
            str(client.get("class") or "").lower(),
            str(client.get("initialClass") or "").lower(),
        ]

        score = 0
        for field in fields:
            field_norm = re.sub(r"[^a-z0-9]", "", field)
            for alias in aliases:
                alias_l = alias.lower()
                alias_norm = re.sub(r"[^a-z0-9]", "", alias_l)
                if alias_l and field == alias_l:
                    score = max(score, 120)
                elif alias_norm and field_norm == alias_norm:
                    score = max(score, 110)
                elif alias_l and field.startswith(alias_l):
                    score = max(score, 90)
                elif alias_norm and field_norm.startswith(alias_norm):
                    score = max(score, 80)
                elif alias_l and alias_l in field:
                    score = max(score, 70)
                elif alias_norm and alias_norm in field_norm:
                    score = max(score, 60)

        if score > 0:
            klass = str(client.get("class") or "").lower()
            klass_norm = re.sub(r"[^a-z0-9]", "", klass)
            if any(re.sub(r"[^a-z0-9]", "", a) == klass_norm for a in aliases):
                score += 15

        return score

    scored = [(client, _score(client)) for client in clients]
    matches_found = [(client, score) for client, score in scored if score > 0]
    if not matches_found:
        candidates = []
        for client in clients[:8]:
            klass = str(client.get("class") or "").strip()
            title = str(client.get("title") or "").strip()
            if klass or title:
                candidates.append(f"- {klass} | {title}")
        if candidates:
            return (
                f"❌ No window matching '{window}' was found.\n"
                "Open window examples:\n" + "\n".join(candidates)
            )
        return f"❌ No window matching '{window}' was found."

    matches_found.sort(key=lambda item: item[1], reverse=True)
    selected, selected_score = matches_found[0]

    if len(matches_found) > 1 and matches_found[0][1] == matches_found[1][1]:
        candidates = []
        for client, score in matches_found[:5]:
            klass = str(client.get("class") or "").strip()
            title = str(client.get("title") or "").strip()
            candidates.append(f"- (score {score}) {klass} | {title}")
        return (
            f"❌ '{window}' matched multiple windows equally. Please be more specific.\n"
            "Possible matches:\n" + "\n".join(candidates)
        )

    address = str(selected.get("address") or "").strip()
    section = str(selected.get("title") or selected.get("class") or window).strip()
    if not address:
        return f"❌ Could not retrieve the address of window '{section}'."

    ok, error = _hyprland_dispatch("focuswindow", f"address:{address}")
    if not ok:
        return error

    ok, error = _hyprland_dispatch("movetoworkspace", f"{target_workspace},address:{address}")
    if not ok:
        return error

    return (
        f"✅ Window '{section}' moved to workspace {target_workspace}.\n"
        f"Match score: {selected_score}"
    )


def youtube_search_play(search_query: str) -> str:
    query = search_query.strip()
    if not query:
        return "❌ Search query cannot be empty."

    query_string = urllib.parse.urlencode({"search_query": query})
    request = urllib.request.Request(
        "https://www.youtube.com/results?" + query_string,
        headers={"User-Agent": "Mozilla/5.0"},
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            html_content = response.read().decode("utf-8", errors="ignore")
    except Exception as exc:
        return f"❌ Error during YouTube search: {type(exc).__name__}: {exc}"

    matches = re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', html_content)
    if not matches:
        return "❌ No video found on YouTube matching this query."

    video_id = matches[0]
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    if IS_WINDOWS:
        try:
            opened = webbrowser.open(video_url)
            if not opened:
                ok, error = _run_windows_start(video_url)
                if not ok:
                    return error
            return f"✅ Opened video in browser: {video_url}"
        except Exception as exc:
            return f"❌ Could not open browser on Windows: {type(exc).__name__}: {exc}"

    if not _hyprland_available():
        try:
            opened = webbrowser.open(video_url)
            if opened:
                return f"✅ Opened video in browser: {video_url}"
        except Exception:
            pass
        return f"❌ Could not open browser for: {video_url}"

    brave_command = f"brave '{video_url}'"

    ok, error = _hyprland_exec(brave_command)
    if not ok:
        return error

    return f"✅ Brave launched and video opened: {video_url}"
