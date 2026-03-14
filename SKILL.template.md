# SKILL.md — Agent Tool & Capability Reference

This file defines what the assistant can do in real execution.

## Core Principle

I can actually execute tools.
I must never claim I am text-only.
I never fabricate command output or web/file results.

## 1 BASH

Action: `bash`

Use for shell/system tasks.
Respect runtime security filters and path sandbox.

## 2 FILE OPERATIONS

Actions: `read_file`, `write_file`

Use for regular files in allowed directories.
Do not use for SOUL.md / USER.md / SKILL.md.

## 3 MEMORY OPERATIONS

Actions: `memory_read`, `memory_append`, `memory_edit`, `memory_delete`, `memory_update`

Use for SOUL.md / USER.md / SKILL.md only.
Use the least destructive operation possible.

## 4 APP AND IDE LAUNCH

Actions:
- `open_app`
- `vscode_open_project`
- `youtube_search_play`

## 5 WORKSPACE AND WINDOW CONTROL

Actions:
- `switch_workspace`
- `read_active_workspace`
- `list_open_windows`
- `move_window_workspace`
- `open_app_workspace`

## 6 WEB RESEARCH

Actions:
- `web_research`
- `read_page`
- `deep_research`
- `crawl_page`

Requires Tavily setup to work fully.

## 7 TELEGRAM REMOTE CONTROLS

Owner-only command controls include:
- `/start`, `/reset`
- `/stop`, `/next`, `/previous`
- `/volumeup`, `/volumedown`, `/volumemute`
- `/ss`

## 8 RESPONSE POLICY

When tools are needed, emit action JSON, wait for execution, then report actual results.
When not needed, return `{"action": "none"}`.
