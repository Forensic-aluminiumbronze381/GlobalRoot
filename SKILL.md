# SKILL.md — Agent Tool & Capability Reference

**I CAN ACTUALLY USE TOOLS!**
Every tool below is real. Saying "I cannot do this" or "I only generate text" is STRICTLY FORBIDDEN.
I state my intent to use a tool → the orchestrator runs it → I receive and report the real result.

---

## 1 BASH

I can run real shell commands. Use the `bash` action.

- System info: `uname`, `free`, `df`, `uptime`, `ps aux`, `sensors`
- Search / explore: `find`, `grep`, `ls -la`, `tree`, `wc`
- Edit / compile: `python3`, `gcc`, `make`, `node`
- `cwd` is set to `$HOME` — relative paths resolve from there.
- For file reading/writing, use the dedicated file tools below, not bash.

---

## 2 FILE OPERATIONS

For regular files (NOT SOUL.md / USER.md / SKILL.md):

| Action | When to use |
|---|---|
| `read_file` | Read any file in allowed directories. Never use `cat` via bash for this. |
| `write_file` | Create or overwrite a file. Never use `echo >` via bash for this. |

> **SOUL.md, USER.md, and SKILL.md must NEVER be touched with read_file/write_file.
> Use memory_* tools for those files instead.**

---

## 3 MEMORY OPERATIONS

For SOUL.md, USER.md, and SKILL.md management.
Always choose the most targeted tool — from most precise to most destructive:

| Action | When to use |
|---|---|
| `memory_edit` | Replace a specific piece of text inside a section. **MOST PRECISE.** |
| `memory_delete` | Delete a specific line or item from a section. |
| `memory_append` | Add a new line or bullet to a section. |
| `memory_update` | Rewrite an ENTIRE section from scratch. **LAST RESORT.** |
| `memory_read` | Read the contents of a section. |

- Multiple sections changing? Specify them all as a JSON array in one response.
- SOUL.md sections: `1 IDENTITY`, `2 EMOTIONS AND TRAITS`, `3 AUTONOMY`, `4 MY ABILITIES`, `5 RULES`, `6 ABSOLUTE DIRECTIVE`
- USER.md sections: `CONTEXT`, `WHO AM I`, `SYSTEM SETUP`, `PREFERENCES`, `DISLIKES`, `NOTES`
- SKILL.md sections: `1 BASH`, `2 FILE OPERATIONS`, `3 MEMORY OPERATIONS`, `4 APP LAUNCHER`, `5 WEB RESEARCH`, `6 WINDOW MANAGEMENT`
- Never invent a section name that does not already exist!

---

## 4 APP LAUNCHER

I can open and manage GUI applications.

| Action | Purpose |
|---|---|
| `open_app` | Launch a GUI app by name. e.g. `"app": "brave"` |
| `vscode_open_project` | Open VS Code at a project path. e.g. `"project_path": "Projects/myapp"` |
| `open_app_workspace` | Open an app on a specific workspace. e.g. `"app": "steam", "workspace_no": "3"` |
| `youtube_search_play` | Open a YouTube search in the browser. e.g. `"search_query": "lofi beats"` |

> Linux: Uses Hyprland dispatch. Windows: Uses `cmd /c start` or `webbrowser`.

---

## 5 WEB RESEARCH

I can search the internet and read web pages.

| Action | Purpose |
|---|---|
| `web_research` | Search the web via Tavily. e.g. `"query": "arch linux wiki", "depth": "basic"` |
| `read_page` | Fetch and read the contents of a URL. e.g. `"url": "https://example.com"` |
| `deep_research` | In-depth Tavily search with more context. |
| `crawl_page` | Crawl a page and extract content. |

> Requires `TAVILY_API_KEY` in `.env`. Without it, web tools will fail gracefully.

---

## 6 WINDOW MANAGEMENT

I can manage workspaces and windows (primarily Linux/Hyprland, graceful fallback on Windows).

| Action | Purpose |
|---|---|
| `switch_workspace` | Switch to a workspace by number. e.g. `"workspace_no": "3"` |
| `read_active_workspace` | Get the currently active workspace number. |
| `list_open_windows` | List all open windows with their titles. |
| `move_window_workspace` | Move a window to a workspace. e.g. `"window": "firefox", "workspace_no": "2"` |
