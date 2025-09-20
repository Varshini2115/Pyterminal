import os
import sys
import re
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter, PathCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers.shell import BashLexer
from terminal.core import Terminal
from terminal.commands import pwd, ls, cd, mkdir, rm, help_cmd
from terminal.monitor import monitor_cmd
from terminal.nl_parser import parse_natural_language, get_command_suggestions

# Define styles for syntax highlighting
style = Style.from_dict({
    'command': '#00AA00 bold',  # Green for commands
    'path': '#0000AA',          # Blue for paths
    'option': '#AA00AA',        # Purple for options
    'error': '#AA0000',         # Red for errors
    'output': '#AAAAAA',        # Gray for output
})

def get_completer(terminal):
    """Create a completer for the terminal commands and file paths"""
    commands = list(terminal.commands.keys())
    command_completer = WordCompleter(commands, sentence=True)
    path_completer = PathCompleter()
    
    def combined_completer(text, complete_event):
        # If we're at the start of the line, use command completer
        if not ' ' in text:
            return command_completer.get_completions(text, complete_event)
        # Otherwise use path completer
        else:
            return path_completer.get_completions(text, complete_event)
    
    return combined_completer

def main():
    # Create terminal instance
    terminal = Terminal()
    
    # Register commands
    terminal.register_command("pwd", pwd, "Print working directory")
    terminal.register_command("ls", ls, "List directory contents")
    terminal.register_command("cd", cd, "Change directory")
    terminal.register_command("mkdir", mkdir, "Create a directory")
    terminal.register_command("rm", rm, "Remove files or directories")
    terminal.register_command("help", help_cmd, "Display help information")
    terminal.register_command("monitor", monitor_cmd, "Display system monitoring information")
    terminal.register_command("touch", lambda t, *args: open(os.path.join(t.current_dir, args[0]), 'a').close() or f"Created file: {args[0]}", "Create an empty file")
    terminal.register_command("cat", lambda t, *args: open(os.path.join(t.current_dir, args[0]), 'r').read(), "Display file contents")
    
    # Set up command completion for readline (for non-prompt_toolkit contexts)
    terminal.setup_autocomplete()
    
    # Create prompt session with history and completion
    history_file = os.path.expanduser("~/.pyterminal_history")
    session = PromptSession(
        history=FileHistory(history_file),
        completer=get_completer(terminal),
        lexer=PygmentsLexer(BashLexer),
        style=style
    )
    
    print("PyTerminal - A Python-based Terminal")
    print("Type 'help' for available commands or use natural language")
    print("Type 'exit' to quit")
    print("Use TAB for command and path auto-completion")
    
    while True:
        try:
            # Get user input with auto-completion and syntax highlighting
            user_input = session.prompt(terminal.get_prompt())
            
            # Check for exit command
            if user_input.strip().lower() == "exit":
                break
            
            # Parse natural language if it doesn't look like a command
            if user_input and not user_input.split()[0] in terminal.commands:
                # Check for command suggestions first
                suggestions = get_command_suggestions(user_input, terminal)
                if len(suggestions) == 1:
                    # Single suggestion - use it
                    suggested_cmd = suggestions[0]
                    print(f"Did you mean: {suggested_cmd}?")
                    user_input = suggested_cmd + (" " + " ".join(user_input.split()[1:]) if len(user_input.split()) > 1 else "")
                elif len(suggestions) > 1:
                    # Multiple suggestions
                    print(f"Did you mean one of these: {', '.join(suggestions)}?")
                
                # Try natural language parsing
                parsed_cmd = parse_natural_language(terminal, user_input)
                if parsed_cmd != user_input:
                    print(f"Interpreted as: {parsed_cmd}")
                    user_input = parsed_cmd
            
            # Execute the command
            result = terminal.execute(user_input)
            if result:
                print(result)
                
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        except Exception as e:
            print(f"Error: {str(e)}")
    
    print("Goodbye!")

if __name__ == "__main__":
    main()