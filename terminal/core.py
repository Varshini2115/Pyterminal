import os
import shutil
import sys
from pathlib import Path

# Use pyreadline3 on Windows, readline on Unix
try:
    if sys.platform == 'win32':
        import pyreadline3 as readline
    else:
        import readline
except ImportError:
    # Fallback if readline is not available
    readline = None

from terminal.nl_parser import update_context

class Terminal:
    def __init__(self):
        self.current_dir = os.getcwd()
        self.commands = {}
        self.history = []
        self.command_suggestions = []
        self.last_executed_command = ""
    
    def register_command(self, name, func, help_text="No help available"):
        """Register a command with the terminal"""
        self.commands[name] = {
            'func': func,
            'help': help_text
        }
    
    def get_command_completions(self, text, state):
        """Return command completions for readline"""
        # Get all command names that start with the text
        if state == 0:
            self.command_suggestions = [cmd for cmd in self.commands.keys() if cmd.startswith(text)]
            
            # Add file/directory completions if not a command start
            if not self.command_suggestions and ' ' in readline.get_line_buffer():
                # We're completing an argument, not a command
                path_to_complete = text
                if not os.path.isabs(path_to_complete):
                    path_to_complete = os.path.join(self.current_dir, path_to_complete)
                
                dir_path = os.path.dirname(path_to_complete) or '.'
                file_prefix = os.path.basename(path_to_complete)
                
                try:
                    self.command_suggestions = [os.path.join(dir_path, f) for f in os.listdir(dir_path) 
                                              if f.startswith(file_prefix)]
                except:
                    self.command_suggestions = []
        
        # Return the state-th suggestion, or None if no more suggestions
        return self.command_suggestions[state] if state < len(self.command_suggestions) else None
    
    def execute(self, command_line):
        """Execute a command"""
        if not command_line.strip():
            return ""
            
        self.history.append(command_line)
        self.last_executed_command = command_line
        
        # Parse the command line
        parts = command_line.split()
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        # Execute the command if it exists
        result = ""
        if command in self.commands:
            try:
                result = self.commands[command]['func'](self, *args)
                # Update context with the executed command and its result
                update_context(command_line, result)
                return result
            except Exception as e:
                return f"Error: {str(e)}"
        else:
            return f"Command not found: {command}"
    
    def get_prompt(self):
        """Get the terminal prompt"""
        return f"{self.current_dir} $ "
    
    def setup_autocomplete(self):
        """Set up tab completion for commands"""
        # Set up readline completer if available
        if readline:
            readline.set_completer(self.get_command_completions)
            readline.parse_and_bind("tab: complete")
            readline.set_completer_delims(" \t\n")
            return True
        return False