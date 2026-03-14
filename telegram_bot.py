"""
{ASSISTANT_NAME} Telegram Interface
  Runs the dual-pass agent architecture via Telegram instead of the terminal.
  No streaming — returns a single complete reply.
  Security: Only OWNER_CHAT_ID can send messages.
"""
import os
import sys
import re
import logging
import tempfile
import subprocess
from pathlib import Path

import telebot

from core.llm import consciousness_call, action_intent_call, executor_call, is_alive
from core.memory import Memory, EntityTracker, trim_history
from tools.bash import bash
from tools.read_file_tool import read_file
from tools.write_file_tool import write_file
from tools.memory_tools import (
    append_to_memory, update_section, read_section, edit_line, delete_line,
)
from tools.app_launcher import (
    open_app, open_app_workspace, youtube_search_play, switch_workspace,
    read_active_workspace, list_open_windows, move_window_workspace, vscode_open_project,
)
from tools.tavily_tools import web_research, read_page
from config import (
    TELEGRAM_TOKEN, OWNER_CHAT_ID, USER_NAME, ASSISTANT_NAME,
    BASE_MAX_LOOPS, EXTENDED_MAX_LOOPS,
)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("root-telegram")



def load_system() -> str:
    base_dir = Path(__file__).parent
    parts = []
    for fname in ["SOUL.md", "SKILL.md", "USER.md"]:
        p = base_dir / fname
        if p.exists():
            parts.append(p.read_text(encoding="utf-8"))
            log.info("%s loaded (%d characters)", fname, len(parts[-1]))
        else:
            log.warning("%s not found: %s", fname, p)
    return "\n\n---\n\n".join(parts)



def execute_tool(action: dict) -> str:
    action_name = action.get("action", "none")
    try:
        if action_name == "bash":
            return bash(action.get("command", ""))
        elif action_name == "read_file":
            return read_file(action.get("file", ""))
        elif action_name == "write_file":
            return write_file(action.get("file", ""), action.get("content", ""))
        elif action_name == "memory_append":
            return append_to_memory(
                action.get("file", ""), action.get("section", ""), action.get("content", ""),
            )
        elif action_name == "memory_update":
            return update_section(
                action.get("file", ""), action.get("section", ""), action.get("new_content", ""),
            )
        elif action_name == "memory_read":
            return read_section(action.get("file", ""), action.get("section", ""))
        elif action_name == "memory_edit":
            return edit_line(
                action.get("file", ""), action.get("section", ""),
                action.get("old", ""), action.get("new", ""),
            )
        elif action_name == "memory_delete":
            return delete_line(
                action.get("file", ""), action.get("section", ""), action.get("to_delete", ""),
            )
        elif action_name == "open_app":
            return open_app(action.get("app", ""))
        elif action_name == "vscode_open_project":
            return vscode_open_project(action.get("project_path", ""))
        elif action_name == "switch_workspace":
            return switch_workspace(action.get("workspace_no", ""))
        elif action_name == "open_app_workspace":
            return open_app_workspace(
                action.get("app", ""), action.get("workspace_no", ""),
            )
        elif action_name == "read_active_workspace":
            return read_active_workspace()
        elif action_name == "list_open_windows":
            return list_open_windows()
        elif action_name == "move_window_workspace":
            return move_window_workspace(
                action.get("window", ""), action.get("workspace_no", ""),
            )
        elif action_name == "youtube_search_play":
            return youtube_search_play(action.get("search_query", ""))
        elif action_name == "web_research":
            return web_research(action.get("query", ""), action.get("depth", "advanced"))
        elif action_name == "read_page":
            return read_page(action.get("url", ""))
        elif action_name == "deep_research":
            from tools.tavily_tools import deep_research
            return deep_research(action.get("query", ""))
        elif action_name == "crawl_page":
            from tools.tavily_tools import crawl_page
            return crawl_page(action.get("url", ""))
        else:
            return f"Invalid action: {action_name}"
    except Exception as e:
        return f"Tool error: {type(e).__name__}: {e}"



_state = {
    "memory": None,
    "tracker": None,
    "history": [],
    "system": "",
}


def _extract_requested_workspace(text: str) -> str | None:
    t = text.lower()
    patterns = [
        r"workspace\s*(\d+)",
        r"(\d+)\s*\.?\s*workspace",
    ]
    for p in patterns:
        m = re.search(p, t)
        if not m:
            continue
        raw = m.group(1)
        if not raw.isdigit():
            continue
        n = int(raw)
        if n == 0:
            return "10"
        if 1 <= n <= 10:
            return str(n)
    return None


def _init_state():
    if _state["memory"] is None:
        _state["memory"] = Memory()
        _state["tracker"] = EntityTracker()
        _state["system"] = load_system()
        log.info("State initialized.")


def process_message(user_input: str) -> str:
    """
    Processes a single user message through the dual-pass architecture
    and returns the final response as plain text.
    """
    _init_state()
    memory: Memory = _state["memory"]
    tracker: EntityTracker = _state["tracker"]
    history: list = _state["history"]
    system: str = _state["system"]

    past = memory.recall(user_input)
    active_system = system
    if past:
        active_system += (
            f"\n\n<past_memory>\n"
            f"The following is past context recalled from previous conversations:\n{past}\n"
            f"</past_memory>"
        )

    history.append({"role": "user", "content": user_input})

    max_loops = BASE_MAX_LOOPS
    error_count = 0
    executed_actions = set()
    accumulated_results = []  
    last_consciousness = ""   

    for loop in range(max_loops):
        log.info("Loop %d/%d", loop + 1, max_loops)
        consciousness = consciousness_call(history, system=active_system)
        if not consciousness:
            consciousness = f"({ASSISTANT_NAME} did not produce a response)"

        last_consciousness = consciousness

        has_action = action_intent_call(user_input, consciousness)

        if not has_action:
            log.info("No action intent, loop ended.")
            history.append({"role": "assistant", "content": consciousness})
            memory.save(user_input, consciousness)
            break

        entity_ctx = tracker.get_context()
        actions = executor_call(
            user_input,
            consciousness,
            entity_ctx,
            allow_regex_fallback=(loop == 0),
        )

        requested_workspace = _extract_requested_workspace(user_input)
        if requested_workspace:
            guarded_actions = []
            for a in actions:
                action = a.get("action", "none")
                guarded = dict(a)

                if action == "open_app":
                    guarded["action"] = "open_app_workspace"
                    guarded["workspace_no"] = requested_workspace
                elif action in {"open_app_workspace", "switch_workspace", "move_window_workspace"}:
                    current = str(guarded.get("workspace_no", "")).strip()
                    if current != requested_workspace:
                        log.info(
                            "Guardrail workspace override: %s %s -> %s",
                            action,
                            current or "-",
                            requested_workspace,
                        )
                    guarded["workspace_no"] = requested_workspace

                guarded_actions.append(guarded)
            actions = guarded_actions

        if all(a.get("action", "none") == "none" for a in actions):
            log.info("Executor: none")
            history.append({"role": "assistant", "content": consciousness})
            memory.save(user_input, consciousness)
            break

        history.append({"role": "assistant", "content": consciousness})

        seen = set()
        unique = []
        for a in actions:
            key = str(sorted(a.items()))
            if key not in seen:
                seen.add(key)
                unique.append(a)

        all_results = []
        accumulated_results_web = False
        for action_dict in unique:
            action_name = action_dict.get("action", "none")
            if action_name == "none":
                continue

            _WEB_TOOLS = {"web_research", "read_page", "deep_research", "crawl_page"}
            action_key = str(sorted(action_dict.items()))
            type_key = f"__type__{action_name}"
            if action_key in executed_actions or (action_name in _WEB_TOOLS and type_key in executed_actions):
                log.info("Skipped (already executed): %s", action_name)
                continue
            executed_actions.add(action_key)
            if action_name in _WEB_TOOLS:
                executed_actions.add(type_key)

            detail = action_dict.get("command", "") or action_dict.get("file", "") or "-"
            log.info("Action: %s | %s", action_name, detail)
            result = execute_tool(action_dict)
            log.info("Tool output: %s", result[:300])
            all_results.append(result)
            if action_name in {"web_research", "read_page"} and not result.startswith("❌"):
                accumulated_results_web = True
            tracker.update(action_dict)

        if not all_results:
            log.info("All actions already executed, stopping loop.")
            break

        combined = "\n".join(all_results)
        accumulated_results.extend(all_results)

        failed = sum(1 for r in all_results if r.startswith("\u274c"))
        error_count = error_count + failed if failed > 0 else 0
        if error_count >= 3:
            log.warning("3+ consecutive errors, stopping loop.")
            break

        _observation_suffix = (
            "\nWARNING: Web research ('web_research'/'read_page') has ALREADY been completed this round. "
            "Do NOT use these tools AGAIN. Present the result to the user and finish."
            if accumulated_results_web else ""
        )
        history.append({
            "role": "user",
            "content": (
                f"OBSERVATION RESULT (command ALREADY executed, do not re-run!):\n{combined}\n\n"
                "Show this result to the user AS-IS. Do NOT run the same command again. "
                "If a DIFFERENT action is needed, state it; otherwise inform the user of the result."
                + _observation_suffix
            ),
        })
        history[:] = trim_history(history)
    else:
        log.warning("Maximum loop limit reached (%d).", max_loops)

    _state["history"] = trim_history(history)

    if accumulated_results:
        tool_output = "\n".join(accumulated_results)
        final_response = last_consciousness + "\n\n" + tool_output
    else:
        final_response = last_consciousness

    log.info("Response to send (%d chars): %s", len(final_response), final_response[:200])
    return final_response



def main():
    if not TELEGRAM_TOKEN:
        print("TELEGRAM_TOKEN is not set!")
        print("Usage: TELEGRAM_TOKEN='...' OWNER_CHAT_ID='...' python telegram_bot.py")
        sys.exit(1)

    if not OWNER_CHAT_ID:
        print("OWNER_CHAT_ID is not set!")
        sys.exit(1)

    if not is_alive():
        print("Ollama is not running. Start it with: ollama serve")
        sys.exit(1)

    bot = telebot.TeleBot(TELEGRAM_TOKEN)
    log.info("%s Telegram bot starting... (Owner ID: %d)", ASSISTANT_NAME, OWNER_CHAT_ID)

    def _run_command_variants(command_variants: list[list[str]]) -> tuple[bool, str]:
        """Tries the first working command variant and returns the output."""
        errors: list[str] = []
        for cmd in command_variants:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            except FileNotFoundError:
                errors.append(f"not found: {cmd[0]}")
                continue
            except subprocess.TimeoutExpired:
                errors.append(f"timeout: {' '.join(cmd)}")
                continue

            if result.returncode == 0:
                out = (result.stdout or "").strip()
                return True, out

            err = (result.stderr or result.stdout or "command failed").strip()
            errors.append(f"{' '.join(cmd)} -> {err}")

        return False, " | ".join(errors) if errors else "command could not be executed"

    def _handle_media_action(action: str) -> str:
        if os.name == "nt":
            return "❌ Media key adapter is not available on Windows in this build."

        if action == "stop":
            ok, detail = _run_command_variants([
                ["playerctl", "play-pause"],
                ["playerctl", "pause"],
            ])
            return "✅ /stop applied (fn+f9 equivalent)." if ok else f"❌ /stop failed: {detail}"

        if action == "next":
            ok, detail = _run_command_variants([
                ["playerctl", "next"],
            ])
            return "✅ /next applied (fn+f10 equivalent)." if ok else f"❌ /next failed: {detail}"

        if action == "previous":
            ok, detail = _run_command_variants([
                ["playerctl", "previous"],
            ])
            return "✅ /previous applied (fn+f8 equivalent)." if ok else f"❌ /previous failed: {detail}"

        if action == "volumeup":
            ok, detail = _run_command_variants([
                ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%+"],
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"],
            ])
            return "✅ /volumeup applied (fn+f7 equivalent)." if ok else f"❌ /volumeup failed: {detail}"

        if action == "volumedown":
            ok, detail = _run_command_variants([
                ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%-"],
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-5%"],
            ])
            return "✅ /volumedown applied (fn+f6 equivalent)." if ok else f"❌ /volumedown failed: {detail}"

        if action == "volumemute":
            ok, detail = _run_command_variants([
                ["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"],
                ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"],
            ])
            return "✅ /volumemute applied (fn+f5 equivalent)." if ok else f"❌ /volumemute failed: {detail}"

        return "❌ Unknown media action."

    @bot.message_handler(commands=["start"])
    def cmd_start(message):
        if message.chat.id != OWNER_CHAT_ID:
            bot.reply_to(message, "Access denied.")
            return
        bot.reply_to(message, f"{ASSISTANT_NAME} is active. Dual-Pass Architecture ready.")

    @bot.message_handler(commands=["reset"])
    def cmd_reset(message):
        if message.chat.id != OWNER_CHAT_ID:
            return
        _state["history"] = []
        bot.reply_to(message, "Conversation history cleared.")

    @bot.message_handler(commands=["stop"])
    def cmd_stop(message):
        if message.chat.id != OWNER_CHAT_ID:
            bot.reply_to(message, "Access denied.")
            return
        bot.reply_to(message, _handle_media_action("stop"))

    @bot.message_handler(commands=["next"])
    def cmd_next(message):
        if message.chat.id != OWNER_CHAT_ID:
            bot.reply_to(message, "Access denied.")
            return
        bot.reply_to(message, _handle_media_action("next"))

    @bot.message_handler(commands=["previous"])
    def cmd_previous(message):
        if message.chat.id != OWNER_CHAT_ID:
            bot.reply_to(message, "Access denied.")
            return
        bot.reply_to(message, _handle_media_action("previous"))

    @bot.message_handler(commands=["volumeup"])
    def cmd_volumeup(message):
        if message.chat.id != OWNER_CHAT_ID:
            bot.reply_to(message, "Access denied.")
            return
        bot.reply_to(message, _handle_media_action("volumeup"))

    @bot.message_handler(commands=["volumedown"])
    def cmd_volumedown(message):
        if message.chat.id != OWNER_CHAT_ID:
            bot.reply_to(message, "Access denied.")
            return
        bot.reply_to(message, _handle_media_action("volumedown"))

    @bot.message_handler(commands=["volumemute"])
    def cmd_volumemute(message):
        if message.chat.id != OWNER_CHAT_ID:
            bot.reply_to(message, "Access denied.")
            return
        bot.reply_to(message, _handle_media_action("volumemute"))

    @bot.message_handler(commands=["ss"])
    def cmd_screenshot(message):
        if message.chat.id != OWNER_CHAT_ID:
            bot.reply_to(message, "Access denied.")
            return

        bot.reply_to(message, "\U0001f4f8 Taking screenshot...")

        ss_path = str(Path(tempfile.gettempdir()) / "root_vision.png")

        if os.name == "nt":
            escaped_ss_path = ss_path.replace("'", "''")
            ps_script = (
                "Add-Type -AssemblyName System.Windows.Forms;"
                "Add-Type -AssemblyName System.Drawing;"
                "$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds;"
                "$bmp = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height);"
                "$g = [System.Drawing.Graphics]::FromImage($bmp);"
                "$g.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size);"
                f"$bmp.Save('{escaped_ss_path}');"
                "$g.Dispose();"
                "$bmp.Dispose();"
            )
            ret = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if ret.returncode != 0:
                detail = (ret.stderr or ret.stdout or "unknown error").strip()
                bot.reply_to(message, f"Could not take screenshot on Windows: {detail}")
                return
        else:
            ret = os.system(f"grim {ss_path}")
            if ret != 0:
                bot.reply_to(message, "grim command failed. Could not take screenshot.")
                return

        try:
            with open(ss_path, "rb") as photo:
                bot.send_photo(message.chat.id, photo)
            os.remove(ss_path)
        except Exception as e:
            bot.reply_to(message, f"Error sending image: {e}")

    @bot.message_handler(func=lambda m: True)
    def handle_message(message):
        if message.chat.id != OWNER_CHAT_ID:
            bot.reply_to(message, f"You are not {USER_NAME}. Access denied.")
            log.warning("UNAUTHORIZED ACCESS ATTEMPT! ID: %d", message.chat.id)
            return

        user_input = (message.text or "").strip()
        if not user_input:
            return

        log.info("Message received: %s", user_input[:80])

        bot.send_chat_action(message.chat.id, "typing")

        try:
            response = process_message(user_input)
        except Exception as e:
            log.exception("process_message error")
            response = f"An error occurred: {e}"

        MAX_TG_LEN = 4096
        if len(response) <= MAX_TG_LEN:
            bot.reply_to(message, response)
        else:
            chunks = [response[i:i + MAX_TG_LEN] for i in range(0, len(response), MAX_TG_LEN)]
            for chunk in chunks:
                bot.send_message(message.chat.id, chunk)

    print(f"{ASSISTANT_NAME} Telegram bot started. Owner ID: {OWNER_CHAT_ID}")
    print("Press Ctrl+C to stop.")
    bot.infinity_polling()


if __name__ == "__main__":
    main()
