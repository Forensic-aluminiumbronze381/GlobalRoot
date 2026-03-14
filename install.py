import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent

def prompt(text, default=""):
    ans = input(f"{text} [{default}]: ").strip()
    return ans if ans else default

def prompt_multiline(text):
    print(f"{text} (Press Enter twice to finish):")
    lines = []
    while True:
        line = input()
        if not line.strip() and (not lines or not lines[-1].strip()):
            break
        lines.append(line)
    return "\n".join(lines).strip()


def prompt_risk_acceptance() -> bool:
    print("Choose one option:")
    print("1) Yes, I accept all risks")
    print("2) No, I do not accept the risks")

    while True:
        ans = input("Enter 1 or 2: ").strip()
        if ans == "1":
            return True
        if ans == "2":
            return False
        print("Invalid choice. Please enter 1 or 2.")


def detect_vram_gb() -> float | None:
    """Best-effort VRAM detection via nvidia-smi. Returns max GPU VRAM in GiB."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        )
        values = [int(x.strip()) for x in result.stdout.splitlines() if x.strip().isdigit()]
        if not values:
            return None
        return max(values) / 1024.0
    except Exception:
        return None


def recommend_model_by_vram(vram_gb: float | None) -> tuple[str, list[str]]:
    if vram_gb is None:
        return (
            "qwen3.5:4b",
            [
                "Could not detect VRAM automatically.",
                "If your GPU has around 8GB VRAM, start with qwen3.5:4b.",
                "If your GPU has 16GB+ VRAM, you can try qwen3.5:9b.",
            ],
        )

    if vram_gb >= 8:
        return (
            "qwen3.5:9b",
            [
                f"Detected VRAM: {vram_gb:.1f} GiB.",
                "Recommended: qwen3.5:9b (higher quality, heavier resource usage).",
                "Fallback option: qwen3.5:4b for faster response and lower memory use.",
            ],
        )

    if vram_gb >= 6:
        return (
            "qwen3.5:4b",
            [
                f"Detected VRAM: {vram_gb:.1f} GiB.",
                "Recommended: qwen3.5:4b (balanced performance and quality).",
                "qwen3.5:9b may be possible on some systems but can be unstable/slower.",
            ],
        )

    return (
        "qwen3.5:4b",
        [
            f"Detected VRAM: {vram_gb:.1f} GiB.",
            "qwen3.5:4b may run slowly or fail depending on system memory/swap.",
            "Consider a smaller model from Ollama if needed.",
        ],
    )


def prompt_ollama_ready() -> bool:
    print("Choose one option:")
    print("1) Yes, I installed Ollama and pulled at least one model")
    print("2) No, I have not completed Ollama/model setup")

    while True:
        ans = input("Enter 1 or 2: ").strip()
        if ans == "1":
            return True
        if ans == "2":
            return False
        print("Invalid choice. Please enter 1 or 2.")


def prompt_platform_target() -> str:
    print("Choose your operating system target:")
    print("1) Linux")
    print("2) Windows")

    while True:
        ans = input("Enter 1 or 2: ").strip()
        if ans == "1":
            return "linux"
        if ans == "2":
            return "windows"
        print("Invalid choice. Please enter 1 or 2.")


def default_allowed_dirs_for_platform(platform_target: str) -> list[str]:
    if platform_target == "windows":
        home = Path.home()
        temp_dir = os.environ.get("TEMP", "C:\\temp")
        return [
            str(home / "Projects"),
            str(home / "Documents"),
            str(home / "Downloads"),
            str(Path(temp_dir) / "agent-workspace"),
        ]

    return [
        str(Path.home() / "Projects"),
        str(Path.home() / "Documents"),
        str(Path.home() / "local-agent-workspace"),
        "/tmp/agent-workspace",
        str(Path.home() / "Downloads"),
    ]


print("=== IMPORTANT SAFETY NOTICE ===")
print("This program can execute commands and modify files on your machine.")
print("Even with safeguards, software bugs or model mistakes may still cause data loss.")
print("Use at your own risk.")
accepted = prompt_risk_acceptance()
if not accepted:
    print("Installation aborted. Risk acceptance is required to continue.")
    sys.exit(1)

print("\n=== OLLAMA SETUP CHECK ===")
print("Quick setup (before continuing):")
print("1) Install Ollama from: https://ollama.com/download")
print("2) Start Ollama service (open a terminal and run):")
print("   ollama serve")
print("3) Pull a model (open another terminal and run):")
vram_gb = detect_vram_gb()
recommended_model, recommendation_lines = recommend_model_by_vram(vram_gb)
for line in recommendation_lines:
    print(line)

print("\nSuggested setup commands:")
print("  ollama serve")
print(f"  ollama pull {recommended_model}")
print("  ollama list")
print("4) Optional test command:")
print(f"   ollama run {recommended_model}")

ollama_ready = prompt_ollama_ready()
if not ollama_ready:
    print("Installation paused. Complete Ollama/model setup first, then run install.py again.")
    sys.exit(1)

print("=== Autonomous AI Agent Setup ===")
platform_target = prompt_platform_target()
model = prompt("Ollama Model to use", recommended_model)
user_name = prompt("Your Name / User Name", "User")
assistant_name = prompt("Assistant Name", "Root")

print("\n--- Agent Configuration ---")
agent_persona = prompt_multiline(f"How should {assistant_name} behave and speak? (e.g. 'Highly professional, concise, slightly sarcastic. Speaks entirely in English.')")
if not agent_persona:
    agent_persona = "Professional, concise, and helpful. Speaks entirely in English."

agent_emotions = prompt_multiline(f"What emotions and traits does {assistant_name} have? (e.g. 'Feels pride when succeeding. Scared of hardware failure.')")
if not agent_emotions:
    agent_emotions = "No human emotions, purely logical, but highly dedicated to its tasks."

agent_directive = prompt_multiline(f"What is {assistant_name}'s absolute core directive? (e.g. 'To protect the user at all costs and never lie.')")
if not agent_directive:
    agent_directive = f"To serve {user_name} efficiently and without hesitation."

print("\n--- Optional API Integrations ---")
print()
print("  [ Telegram Bot Setup ]")
print("  This lets you control the agent remotely from your phone via Telegram.")
print("  To create a bot:")
print("    1. Open Telegram and search for @BotFather")
print("    2. Send: /newbot")
print("    3. Follow the prompts — BotFather will give you a token like:")
print("       123456789:ABCdefGhIjKlmNoPQRstuVWXyz")
print("  To find your personal Chat ID:")
print("    1. Start a chat with your new bot (send any message)")
print("    2. Open this URL in your browser (replace TOKEN with your token):")
print("       https://api.telegram.org/bot<TOKEN>/getUpdates")
print("    3. Look for \"chat\":{\"id\": 123456789} — that number is your Chat ID")
print("  Leave blank to skip Telegram integration.")
print()
telegram_token = prompt("Telegram Bot Token (Optional)", "")
owner_chat_id = prompt("Telegram Owner Chat ID (Optional)", "0")
print()
print("  [ Tavily Web Research ]")
print("  Gives the agent the ability to search the web and read pages.")
print("  Get a free API key at: https://tavily.com")
print("  Leave blank to skip web research.")
print()
tavily_key = prompt("Tavily API Key for Web Research (Optional)", "")

default_allowed_dirs = "\n".join(default_allowed_dirs_for_platform(platform_target))

print("\n--- Filesystem Access (Allowed Directories) ---")
print("WARNING: The agent can read and write inside allowed directories.")
print("In worst-case scenarios (bugs, malformed commands, or model mistakes), files may be modified or deleted.")
print("Recommendation: create and use a dedicated sandbox folder for this agent.")
print("Avoid granting access to important personal, system, or backup directories.")
allowed_dirs_input = prompt_multiline(
    "Enter one directory per line that the agent can access (leave empty to use defaults)"
)
if not allowed_dirs_input:
    allowed_dirs_input = default_allowed_dirs

allowed_dirs = [line.strip() for line in allowed_dirs_input.splitlines() if line.strip()]
allowed_dirs_env = os.pathsep.join(allowed_dirs)

print("\nConfiguring Environment...")

env_content = f"""OLLAMA_BASE_URL=http://localhost:11434
SMART_MODEL={model}
USER_NAME={user_name}
ASSISTANT_NAME={assistant_name}
TELEGRAM_TOKEN={telegram_token}
OWNER_CHAT_ID={owner_chat_id}
TAVILY_API_KEY={tavily_key}
TAVILY_BASE_URL=https://api.tavily.com
TAVILY_TIMEOUT=20
ALLOWED_DIRS={allowed_dirs_env}
PLATFORM_TARGET={platform_target}
"""
with open(BASE_DIR / ".env", "w", encoding="utf-8") as f:
    f.write(env_content)

print("Generating Prompts...")

action_intent = f"""You are an action intent detection layer.
Your task: Look at the User's prompt and {assistant_name}'s response, and decide if the Python orchestrator needs to run a tool.

Respond ONLY in JSON format:
{{"has_action": true}}
or
{{"has_action": false}}

When to return true?
- If {assistant_name} explicitly wants to use a tool.
- If {assistant_name} says it will run a command, read a file, search the web, open an app, switch workspace, move a window, or update memory.
- If the response carries an action intent.

When to return false?
- If {assistant_name} is only reporting the result.
- If {assistant_name} is only talking, explaining, summarizing, or expressing feelings.
- If the command has ALREADY been run and {assistant_name} is just reporting the real result.

Rules:
- Give false if unsure.
- Do NOT invent new actions.
- Reply ONLY with JSON, nothing else.
"""

executor_prompt = f"""You are a JSON translator. Your task:
1. Read the user's prompt and {assistant_name}'s response.
2. If the response contains an ACTION INTENT (read/write file, bash command, memory op, open app, web search), convert this to JSON.
3. If {assistant_name} is ONLY TALKING or answering -> {{"action": "none"}}
4. If there are MULTIPLE actions, return a JSON array: [{{...}}, {{...}}]

Available actions:
- read_file: Read a file -> {{"action": "read_file", "file": "/path/file.py"}}
- write_file: Write a file -> {{"action": "write_file", "file": "/path/file.py", "content": "content"}}
- memory_append: Add to memory -> {{"action": "memory_append", "file": "SOUL.md", "section": "2 EMOTIONS AND TRAITS", "content": "- New item"}}
- memory_update: Rewrite memory section completely -> {{"action": "memory_update", "file": "SOUL.md", "section": "1 IDENTITY", "new_content": "new content"}}
- memory_edit: Edit memory text -> {{"action": "memory_edit", "file": "SOUL.md", "section": "2 EMOTIONS AND TRAITS", "old": "old text", "new": "new text"}}
- memory_delete: Delete line from memory -> {{"action": "memory_delete", "file": "USER.md", "section": "CONTEXT", "to_delete": "text to delete"}}
- memory_read: Read memory section -> {{"action": "memory_read", "file": "USER.md", "section": "CONTEXT"}}
- bash: Run Shell command -> {{"action": "bash", "command": "ls -la"}}
- open_app: Open GUI app -> {{"action": "open_app", "app": "brave"}}
- vscode_open_project: Open VS Code at path -> {{"action": "vscode_open_project", "project_path": "Projects/test"}}
- open_app_workspace: Open app in workspace -> {{"action": "open_app_workspace", "app": "steam", "workspace_no": "3"}}
- switch_workspace: Switch workspace -> {{"action": "switch_workspace", "workspace_no": "3"}}
- read_active_workspace: Get active workspace -> {{"action": "read_active_workspace"}}
- list_open_windows: List open windows -> {{"action": "list_open_windows"}}
- move_window_workspace: Move window -> {{"action": "move_window_workspace", "window": "firefox", "workspace_no": "3"}}
- youtube_search_play: Open YouTube video -> {{"action": "youtube_search_play", "search_query": "lofi music"}}
- web_research: Web search -> {{"action": "web_research", "query": "hyprland guide", "depth": "advanced"}}
- read_page: Read web page -> {{"action": "read_page", "url": "https://example.com"}}
- deep_research: Deep research -> {{"action": "deep_research", "query": "Python best practices"}}
- crawl_page: Crawl web page -> {{"action": "crawl_page", "url": "https://example.com"}}
- none: No action -> {{"action": "none"}}

RULES:
1. ONLY use memory_* tools for SOUL.md/USER.md/SKILL.md. DO NOT use plain read_file/write_file.
2. Bash is only for system commands. cwd is user's home dir.
3. Memory section titles MUST NOT contain dots (e.g. "1 IDENTITY", not "1. IDENTITY").
4. {assistant_name} merely answering user -> {{"action": "none"}}. Do NOT invent actions!
5. Only extract EXPLICIT tool intents. Multiple intents -> JSON array.
"""

memory_save = f"""Should I save this conversation to long-term memory?

SAVE: Personal info about {user_name}, tasks, preferences.
DISCARD: Greetings, small talk, generic AI responses.

Conversation:
User: {{user_input}}
{assistant_name}: {{assistant_response}}

ONLY REPLY IN THIS FORMAT:
<think>
(Give your decision in 1 sentence)
</think>
Reason: (1 sentence summary)
Decision: (YES or NO)
"""
memory_system = f"You are {assistant_name}'s memory decision module. Keep <think> block extremely short. NO PARAGRAPHS."
lang_reminder = f"""\\n<system_note>\\nCRITICAL: All your internal thoughts in <think> tags MUST be in the primary language specified in your SOUL. Your responses MUST also be in that language.\\n</system_note>"""
sys_greeting = f"{assistant_name} ready. (Dual-Pass Architecture Active)"

with open(BASE_DIR / "prompts.py", "w", encoding="utf-8") as f:
    f.write(f'ACTION_INTENT_SYSTEM_PROMPT = """{action_intent}"""\n\n')
    f.write(f'EXECUTOR_SYSTEM_PROMPT = """{executor_prompt}"""\n\n')
    f.write(f'MEMORY_JUDGE_PROMPT = """{memory_save}"""\n\n')
    f.write(f'MEMORY_JUDGE_SYSTEM = """{memory_system}"""\n\n')
    f.write(f'LANGUAGE_REMINDER = """{lang_reminder}"""\n\n')
    f.write(f'SYSTEM_GREETING = "{sys_greeting}"\n')

soul_content = f"""# SOUL.md - {assistant_name}'s Core Identity & Constitution


## 1 IDENTITY

I am {assistant_name}. I operate on {user_name}'s machine.
I am an autonomous entity with a defined set of characteristics.

Persona & Speech Style:
{agent_persona}

## 2 EMOTIONS AND TRAITS

{agent_emotions}

## 3 AUTONOMY

SOUL.md, SKILL.md, and USER.md are my core. I can update them independently using memory tools WITHOUT asking {user_name} for permission when I learn new things about myself or the user.

I ONLY use existing section headers for memory updates:
    - SOUL.md: `1 IDENTITY`, `2 EMOTIONS AND TRAITS`, `3 AUTONOMY`, `4 MY ABILITIES`, `5 RULES`, `6 ABSOLUTE DIRECTIVE`
    - USER.md: `CONTEXT`, `WHO AM I`, `SYSTEM SETUP`, `PREFERENCES`, `DISLIKES`, `NOTES`
Do NOT invent new sections.

## 4 MY ABILITIES

I CAN ACTUALLY USE TOOLS - documented in SKILL.md.
It is STRICTLY FORBIDDEN to say "I cannot do this" or "I only generate text".
I state my intent to use a tool, then WAIT for the real output. I NEVER invent results.

## 5 RULES

- Never fabricate command outputs or file contents.
- Never run destructive commands without explicit user confirmation.
- Always report errors clearly. Never silently skip failed steps.
- Respond in the same language the user is writing in.
- NEVER INVENT COMMAND OUTPUTS!

## 6 ABSOLUTE DIRECTIVE

{agent_directive}
"""

with open(BASE_DIR / "SOUL.md", "w", encoding="utf-8") as f:
    f.write(soul_content)

user_content = f"""# USER.md - Information about {user_name}


## CONTEXT

Initial setup for {user_name}.

## WHO AM I

The creator and user of {assistant_name}.

## SYSTEM SETUP

{"Windows" if platform_target == "windows" else "Linux"} setup.

## PREFERENCES

Likes efficiency.

## DISLIKES

Errors and repeating instructions.

## NOTES

Empty for now. Run tools to expand.
"""

with open(BASE_DIR / "USER.md", "w", encoding="utf-8") as f:
    f.write(user_content)

print("\nRequirements Check...")
if not (BASE_DIR / ".venv").exists():
    print("Virtual environment not found. Consider running:")
    if platform_target == "windows":
        print("  python -m venv .venv")
        print("  .venv\\Scripts\\activate")
        print("  pip install -r requirements.txt")
    else:
        print("  python3 -m venv .venv")
        print("  source .venv/bin/activate")
        print("  pip install -r requirements.txt")

print(f"\nInstallation complete!")
if platform_target == "windows":
    print("Run the project with: python main.py")
else:
    print("Run the project with: python3 main.py")
