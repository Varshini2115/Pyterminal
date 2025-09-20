import re
import os
import spacy
from Levenshtein import distance

# Global variables for context awareness
last_command = ""
last_created_file = ""
last_created_dir = ""
last_modified_file = ""

# Load spaCy model - use 'python -m spacy download en_core_web_sm' to download
try:
    nlp = spacy.load("en_core_web_sm")
except:
    # Fallback if model not installed
    print("Warning: spaCy model not found. Using basic NLP parsing.")
    nlp = None

def update_context(command, result):
    """Update context based on executed command"""
    global last_command, last_created_file, last_created_dir, last_modified_file
    
    last_command = command
    
    # Track file/directory creation
    if command.startswith("mkdir "):
        dir_name = command.split(" ", 1)[1]
        last_created_dir = dir_name
    
    # Track file creation/modification
    elif command.startswith("touch ") or command.startswith("echo "):
        # Extract filename from touch command or echo redirection
        if command.startswith("touch "):
            file_name = command.split(" ", 1)[1]
        else:
            # Handle echo with redirection
            match = re.search(r'echo .* > ([\w\d_.-]+)', command)
            if match:
                file_name = match.group(1)
            else:
                file_name = ""
        
        if file_name:
            last_created_file = file_name
            last_modified_file = file_name

def get_command_suggestions(text, terminal):
    """Get command suggestions based on similarity"""
    available_commands = list(terminal.commands.keys())
    suggestions = []
    
    # Split input into words
    words = text.lower().split()
    
    # Check if first word is close to any command
    if words:
        first_word = words[0]
        for cmd in available_commands:
            # Use Levenshtein distance to find similar commands
            if distance(first_word, cmd) <= 2:  # Allow 2 character differences
                suggestions.append(cmd)
    
    return suggestions

def parse_natural_language(terminal, text):
    """Parse natural language commands into terminal commands"""
    global last_command, last_created_file, last_created_dir, last_modified_file
    
    text = text.lower()
    
    # Context-aware commands
    if "last file" in text or "the file i just created" in text:
        if "delete" in text or "remove" in text:
            if last_created_file:
                return f"rm {last_created_file}"
        elif "show" in text or "display" in text or "cat" in text:
            if last_created_file:
                return f"cat {last_created_file}"
    
    if "last directory" in text or "the folder i just created" in text:
        if "delete" in text or "remove" in text:
            if last_created_dir:
                return f"rm -r {last_created_dir}"
        elif "go to" in text or "change to" in text or "cd" in text:
            if last_created_dir:
                return f"cd {last_created_dir}"
    
    if "undo" in text or "revert" in text:
        # Simple undo by returning to previous directory
        if last_command.startswith("cd "):
            return "cd .."
    
    # Use spaCy for more advanced parsing if available
    if nlp:
        doc = nlp(text)
        
        # Extract verbs and nouns
        verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]
        nouns = [token.text for token in doc if token.pos_ == "NOUN"]
        
        # Handle more complex commands based on verb-noun combinations
        if verbs and nouns:
            # File operations
            if any(v in ["create", "make", "add"] for v in verbs):
                if "file" in nouns:
                    # Extract filename
                    for token in doc:
                        if token.pos_ == "PROPN" or (token.pos_ == "NOUN" and token.text != "file"):
                            return f"touch {token.text}"
            
            # Directory navigation
            if any(v in ["go", "navigate", "change", "switch"] for v in verbs):
                if any(n in ["directory", "folder", "path"] for n in nouns):
                    # Extract directory name
                    for token in doc:
                        if token.pos_ == "PROPN" or (token.pos_ == "NOUN" and token.text not in ["directory", "folder", "path"]):
                            return f"cd {token.text}"
    
    # Original regex patterns for backward compatibility
    # Create directory/folder
    if re.search(r'create (a )?(directory|folder|dir) (called |named )?([\w\d_-]+)', text):
        match = re.search(r'create (a )?(directory|folder|dir) (called |named )?([\w\d_-]+)', text)
        folder_name = match.group(4)
        return f"mkdir {folder_name}"
    
    # Move/copy file
    elif re.search(r'(move|copy) ([\w\d_.-]+) (to|into) ([\w\d_/\\-]+)', text):
        match = re.search(r'(move|copy) ([\w\d_.-]+) (to|into) ([\w\d_/\\-]+)', text)
        action = "cp" if match.group(1) == "copy" else "mv"
        file_name = match.group(2)
        destination = match.group(4)
        return f"{action} {file_name} {destination}"
    
    # Delete files
    elif re.search(r'delete (all|the) ([\w\d_.-]+) files', text):
        match = re.search(r'delete (all|the) ([\w\d_.-]+) files', text)
        file_type = match.group(2)
        return f"rm *.{file_type}"
    
    # List files
    elif re.search(r'(list|show) (all |the )?(files|directories)', text):
        return "ls"
    
    # Current directory
    elif re.search(r'(what|where).*current directory', text) or re.search(r'where am i', text):
        return "pwd"
    
    # Check for command suggestions
    suggestions = get_command_suggestions(text, terminal)
    if suggestions:
        if len(suggestions) == 1:
            # If only one suggestion, use it
            return suggestions[0] + (" " + " ".join(text.split()[1:]) if len(text.split()) > 1 else "")
        else:
            # Multiple suggestions
            return text  # Return original, the terminal will show suggestions
    
    # Default: return the original text
    return text