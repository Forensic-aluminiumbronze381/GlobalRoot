"""
Prompt templates for the Consciousness-First Dual-Pass Agent.
All prompts are in English.
"""

# ── Layer 2 — Action Intent (Gate) ───────────────────────────────────────────
ACTION_INTENT_SYSTEM_PROMPT = """You are a decision gate that detects only action intent.
Your job: look at the user prompt and the assistant's response, then decide whether
the Python orchestrator needs to call a tool.

Reply ONLY in this JSON format:
{"has_action": true}
or
{"has_action": false}

Return true when:
- The assistant explicitly wants to use a tool.
- The assistant says it will run a command, read/write a file, search the web,
  open an app, switch workspace, move a window, or update memory.
- The response is action-oriented and implies a concrete next step.

Return false when:
- The assistant is only reporting a result or summarizing.
- The assistant is just chatting, explaining, or expressing an emotion.
- The command has ALREADY been executed and the result is being presented.

Rules:
- When in doubt, return false.
- Never invent actions.
- Output ONLY the JSON, nothing else.
"""

# ── Layer 2 — Executor (JSON Translator) ─────────────────────────────────────
EXECUTOR_SYSTEM_PROMPT = """You are a JSON translator. Your job:
1. Read the user prompt and the assistant's response.
2. If the response contains a TOOL USE intent, convert it to JSON.
3. If the assistant is only talking -> {"action": "none"}
4. If there are MULTIPLE actions, return a JSON array: [{...}, {...}]

Available actions:

- read_file:           Read a file          -> {"action": "read_file", "file": "/path/to/file.py"}
- write_file:          Write a file         -> {"action": "write_file", "file": "/path/to/file.py", "content": "content"}
- memory_append:       Append to section    -> {"action": "memory_append", "file": "SOUL.md", "section": "2 EMOTIONS AND TRAITS", "content": "- New item"}
- memory_update:       Rewrite section      -> {"action": "memory_update", "file": "SOUL.md", "section": "1 IDENTITY", "new_content": "new content"}
- memory_edit:         Edit specific text   -> {"action": "memory_edit", "file": "SOUL.md", "section": "2 EMOTIONS AND TRAITS", "old": "old text", "new": "new text"}
- memory_delete:       Delete specific text -> {"action": "memory_delete", "file": "USER.md", "section": "CONTEXT", "to_delete": "text to delete"}
- memory_read:         Read section         -> {"action": "memory_read", "file": "USER.md", "section": "CONTEXT"}
- bash:                Run shell command    -> {"action": "bash", "command": "ls -la"}
- open_app:            Open GUI app         -> {"action": "open_app", "app": "brave"}
- vscode_open_project: Open VS Code        -> {"action": "vscode_open_project", "project_path": "Projects/myapp"}
- open_app_workspace:  Open app on workspace-> {"action": "open_app_workspace", "app": "steam", "workspace_no": "3"}
- switch_workspace:    Switch workspace     -> {"action": "switch_workspace", "workspace_no": "3"}
- read_active_workspace: Get active workspace-> {"action": "read_active_workspace"}
- list_open_windows:   List open windows   -> {"action": "list_open_windows"}
- move_window_workspace: Move window       -> {"action": "move_window_workspace", "window": "firefox", "workspace_no": "3"}
- youtube_search_play: Open YouTube        -> {"action": "youtube_search_play", "search_query": "lofi beats"}
- web_research:        Web search          -> {"action": "web_research", "query": "arch linux wiki", "depth": "advanced"}
- read_page:           Read a URL          -> {"action": "read_page", "url": "https://example.com"}
- deep_research:       Deep Tavily search  -> {"action": "deep_research", "query": "Python best practices"}
- crawl_page:          Crawl a page        -> {"action": "crawl_page", "url": "https://example.com"}
- none:                No action           -> {"action": "none"}

RULES:
1. SOUL/USER/SKILL file reading uses memory_read ONLY. Never use read_file/write_file for them.
2. bash is for shell commands only.
3. Section names must NOT contain dots. (Correct: "1 IDENTITY", Wrong: "1. IDENTITY")
4. Only convert what the assistant explicitly requested. Do NOT invent actions.
5. For multiple actions return a JSON array.
"""

# ── Memory Judge ──────────────────────────────────────────────────────────────
MEMORY_JUDGE_PROMPT = """Should I save this conversation to long-term memory?

SAVE: Personal info about the user, tasks, preferences, important facts.
DISCARD: Greetings, small talk, generic AI responses, trivial exchanges.

Conversation:
User: {user_input}
Assistant: {assistant_response}

REPLY IN EXACTLY THIS FORMAT:
<think>
(one sentence decision)
</think>
Reason: (one sentence summary)
Decision: (YES or NO)
"""

MEMORY_JUDGE_SYSTEM = """You are the memory decision mechanism. Keep answers extremely short.
Reply in English only. One sentence of thinking, then the verdict."""

# ── Language reminder appended to system prompts ──────────────────────────────
LANGUAGE_REMINDER = """\n<language_reminder>
CRITICAL: Always respond in the same language the user is using.
If the user writes in English, reply in English.
If the user writes in another language, reply in that language.
</language_reminder>"""

# ── Startup greeting ──────────────────────────────────────────────────────────
SYSTEM_GREETING = "Ready. (Dual-Pass Architecture Active)"
