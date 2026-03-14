"""
Consciousness-First Dual-Pass Agent Architecture — Central Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
SMART_MODEL = os.environ.get("SMART_MODEL", "qwen3.5:4b")
USER_NAME = os.environ.get("USER_NAME", "User")
ASSISTANT_NAME = os.environ.get("ASSISTANT_NAME", "Assistant")
PLATFORM_TARGET = os.environ.get("PLATFORM_TARGET", "")

CONSCIOUSNESS_TEMP = 0.7      
EXECUTOR_TEMP = 0.1           
SUMMARY_TEMP = 0.3            

MAX_HISTORY_TOKENS = 6000     
SLIDING_WINDOW_SIZE = 10      
NUM_CTX = 8192                
NUM_PREDICT = 4096            

BASE_MAX_LOOPS = 8            
EXTENDED_MAX_LOOPS = 16       

_PLATFORM_TARGET_NORM = PLATFORM_TARGET.strip().lower()
_IS_WINDOWS_TARGET = (_PLATFORM_TARGET_NORM == "windows") or (os.name == "nt")

_DEFAULT_ALLOWED_DIRS_WINDOWS = [
    str(Path.home() / "Projects"),
    str(Path.home() / "Documents"),
    str(Path.home() / "Downloads"),
    str(Path(os.environ.get("TEMP", "C:\\temp")) / "agent-workspace"),
]

_DEFAULT_ALLOWED_DIRS_LINUX = [
    str(Path.home() / "Projects"),
    str(Path.home() / "Documents"),
    str(Path.home() / "local-agent-workspace"),
    "/tmp/agent-workspace",
    str(Path.home() / "Downloads"),
]

_DEFAULT_ALLOWED_DIRS = _DEFAULT_ALLOWED_DIRS_WINDOWS if _IS_WINDOWS_TARGET else _DEFAULT_ALLOWED_DIRS_LINUX

_ALLOWED_DIRS_RAW = os.environ.get("ALLOWED_DIRS", "")
_ALLOWED_DIRS_NORMALIZED = _ALLOWED_DIRS_RAW.replace("\n", os.pathsep).replace(",", os.pathsep).replace(";", os.pathsep)
ALLOWED_DIRS = [
    str(Path(p.strip()).expanduser())
    for p in _ALLOWED_DIRS_NORMALIZED.split(os.pathsep)
    if p.strip()
] or _DEFAULT_ALLOWED_DIRS

BANNED_COMMANDS = [
    "sudo", "su", "rm -rf /", "mkfs", "dd if=",
    "chmod 777", "chown root", "systemctl", "reboot",
    "shutdown", "poweroff", "pkill -9", "> /dev/sda",
    "wget", "curl -O", "git clone", "pip install",
    "del /f /s /q", "erase /f /s /q", "rmdir /s /q", "rd /s /q",
    "format ", "diskpart", "bcdedit", "reg delete", "cipher /w",
    "remove-item -recurse -force", "remove-item -force -recurse",
    "shutdown /s", "shutdown /r", "shutdown /f", "shutdown /p",
    "restart-computer", "stop-computer"
]

DANGEROUS_PATTERNS = [">/dev/", "> /dev/", "| dd ", "| mkfs", "| sudo", "|sudo"]

BASH_TIMEOUT = 30             
BASH_MAX_OUTPUT = 2000        

CHROMA_PERSIST_DIR = str(Path.home() / ".local/share/jarvis/chroma")
CHROMA_COLLECTION = "root_memory"
MEMORY_TOP_K = 3

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
OWNER_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID", "0"))

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
TAVILY_BASE_URL = os.environ.get("TAVILY_BASE_URL", "https://api.tavily.com")
TAVILY_TIMEOUT = int(os.environ.get("TAVILY_TIMEOUT", "20"))