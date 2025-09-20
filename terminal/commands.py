import os
import shutil
import glob
from pathlib import Path

def pwd(terminal, *args):
    """Print working directory"""
    return terminal.current_dir

def ls(terminal, *args):
    """List directory contents"""
    path = terminal.current_dir
    if args and args[0] != "-l":
        path = os.path.join(terminal.current_dir, args[0])
    
    try:
        items = os.listdir(path)
        if "-l" in args:
            result = []
            for item in items:
                item_path = os.path.join(path, item)
                size = os.path.getsize(item_path)
                is_dir = os.path.isdir(item_path)
                result.append(f"{'d' if is_dir else '-'} {size:8d} {item}")
            return "\n".join(result)
        else:
            return "  ".join(items)
    except Exception as e:
        return f"Error: {str(e)}"

def cd(terminal, *args):
    """Change directory"""
    if not args:
        # Default to home directory
        new_dir = str(Path.home())
    else:
        path = args[0]
        if path == "..":
            new_dir = str(Path(terminal.current_dir).parent)
        elif path.startswith("/") or path.startswith("\\") or path[1:3] == ":\\":
            new_dir = path
        else:
            new_dir = os.path.join(terminal.current_dir, path)
    
    if os.path.isdir(new_dir):
        terminal.current_dir = new_dir
        return ""
    else:
        return f"Error: Directory not found: {new_dir}"

def mkdir(terminal, *args):
    """Create a directory"""
    if not args:
        return "Error: Directory name required"
    
    try:
        path = os.path.join(terminal.current_dir, args[0])
        os.makedirs(path, exist_ok=True)
        return f"Directory created: {args[0]}"
    except Exception as e:
        return f"Error: {str(e)}"

def rm(terminal, *args):
    """Remove files or directories"""
    if not args:
        return "Error: Path required"
    
    recursive = "-r" in args
    if recursive:
        args = [arg for arg in args if arg != "-r"]
    
    if not args:
        return "Error: Path required"
    
    path = os.path.join(terminal.current_dir, args[0])
    
    try:
        if os.path.isdir(path):
            if recursive:
                shutil.rmtree(path)
                return f"Directory removed: {args[0]}"
            else:
                return f"Error: {args[0]} is a directory. Use -r to remove directories."
        else:
            os.remove(path)
            return f"File removed: {args[0]}"
    except Exception as e:
        return f"Error: {str(e)}"

def help_cmd(terminal, *args):
    """Display help information"""
    if args and args[0] in terminal.commands:
        return f"{args[0]}: {terminal.commands[args[0]]['help']}"
    else:
        commands = sorted(terminal.commands.keys())
        return "Available commands:\n" + "\n".join(commands)