"""
File Read Tool — Secure file reading (Path Sandbox)
"""
from pathlib import Path

from config import ALLOWED_DIRS

def is_path_allowed(file_path: Path) -> bool:
    """Check if file path is within allowed directories"""
    resolved = file_path.expanduser().resolve()
    
    for allowed_dir in ALLOWED_DIRS:
        allowed_resolved = Path(allowed_dir).expanduser().resolve()
        try:
            resolved.relative_to(allowed_resolved)
            return True
        except ValueError:
            continue
    
    return False


def read_file(path: str) -> str:
    """Secure file reading. Only reads from allowed directories."""
    try:
        file_path = Path(path).expanduser().resolve()
    except Exception as e:
        return f"❌ Invalid file path: {str(e)}"
    
    if not is_path_allowed(file_path):
        return (
            f"❌ SECURITY: '{path}' is not in allowed directories!\n\n"
            f"Allowed directories:\n" + 
            "\n".join(f"  - {d}" for d in ALLOWED_DIRS)
        )
    
    if not file_path.exists():
        return f"❌ File not found: {file_path}"
    
    if not file_path.is_file():
        return f"❌ This is not a file (probably a directory): {file_path}"
    
    file_size = file_path.stat().st_size
    size_kb = file_size / 1024
    
    try:
        content = file_path.read_text(encoding="utf-8")
        
        MAX_SIZE_KB = 100
        if size_kb > MAX_SIZE_KB:
            char_limit = int(MAX_SIZE_KB * 1024)
            content = content[:char_limit]
            truncated_msg = f"\n\n... (File {size_kb:.1f}KB, truncated at {MAX_SIZE_KB}KB)"
            content += truncated_msg
        
        return (
            f"✅ File read: {file_path}\n"
            f"Size: {size_kb:.1f}KB\n"
            f"Line count: {content.count(chr(10)) + 1}\n"
            f"\n{'='*60}\n\n{content}"
        )
    
    except UnicodeDecodeError:
        return (
            f"❌ File is not in UTF-8 format!\n"
            f"File: {file_path}\n"
            f"This is likely a binary file (image, video, compiled binary, etc.)"
        )
    
    except PermissionError:
        return f"❌ File read permission denied: {file_path}"
    
    except Exception as e:
        return f"❌ READ ERROR: {type(e).__name__}: {str(e)}"


if __name__ == "__main__":
    print(read_file("/tmp/agent-workspace/test.txt"))