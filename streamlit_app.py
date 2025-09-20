import streamlit as st
import os
import time
from terminal.core import Terminal
from terminal.commands import pwd, ls, cd, mkdir, rm, help_cmd
from terminal.monitor import monitor_cmd, get_system_info, get_process_list
from terminal.nl_parser import parse_natural_language
from pygments import highlight
from pygments.lexers.shell import BashLexer
from pygments.formatters import HtmlFormatter

# Add CSS for terminal styling with better contrast
st.markdown("""
<style>
    .terminal-input { 
        color: #00AA00; 
        font-weight: bold; 
        font-family: monospace;
    }
    .terminal-command { 
        color: #0000AA; 
        font-weight: bold; 
        font-family: monospace;
    }
    .terminal-path { 
        color: #AA00AA; 
        font-family: monospace;
    }
    .terminal-output {
        background-color: #1E1E1E;
        color: #FFFFFF;
        padding: 10px;
        border-radius: 5px;
        font-family: monospace;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'terminal' not in st.session_state:
    st.session_state.terminal = Terminal()
    st.session_state.history = []
    st.session_state.output = ""
    
    # Register commands
    st.session_state.terminal.register_command("pwd", pwd, "Print working directory")
    st.session_state.terminal.register_command("ls", ls, "List directory contents")
    st.session_state.terminal.register_command("cd", cd, "Change directory")
    st.session_state.terminal.register_command("mkdir", mkdir, "Create a directory")
    st.session_state.terminal.register_command("rm", rm, "Remove files or directories")
    st.session_state.terminal.register_command("help", help_cmd, "Display help information")
    st.session_state.terminal.register_command("monitor", monitor_cmd, "Display system monitoring information")

# Set up the page
st.set_page_config(page_title="PyTerminal Web", layout="wide")
st.title("PyTerminal Web Interface")

# Create two columns - one for terminal, one for monitoring
col1, col2 = st.columns([2, 1])

with col2:
    st.header("System Monitor")
    
    # Create placeholders for updating metrics
    cpu_metric = st.empty()
    mem_metric = st.empty()
    disk_metric = st.empty()
    
    st.subheader("Top Processes")
    processes_table = st.empty()

# Function to update system metrics
def update_metrics():
    info = get_system_info()
    processes = get_process_list(5)
    
    # Update metrics
    cpu_metric.metric("CPU Usage", f"{info['cpu']}%")
    mem_metric.metric("Memory Usage", f"{info['memory']['percent']}%", 
                     f"{info['memory']['available'] // (1024*1024)} MB free")
    disk_metric.metric("Disk Usage", f"{info['disk']['percent']}%", 
                      f"{info['disk']['free'] // (1024*1024*1024)} GB free")
    
    # Update process table
    process_data = {"PID": [], "Name": [], "Memory %": [], "CPU %": []}
    for proc in processes:
        process_data["PID"].append(proc['pid'])
        process_data["Name"].append(proc['name'])
        process_data["Memory %"].append(f"{proc['memory_percent']:.1f}%")
        process_data["CPU %"].append(f"{proc['cpu_percent']:.1f}%")
    
    processes_table.dataframe(process_data)

# Update metrics on page load
update_metrics()

with col1:
    st.header("Terminal")
    
    # Display terminal output with HTML formatting
    st.markdown("<h3>Output</h3>", unsafe_allow_html=True)
    st.markdown(f"<div class='terminal-output' style='height: 300px; overflow-y: auto;'>{st.session_state.output}</div>", unsafe_allow_html=True)
    
    # Command input
    with st.form(key="command_form", clear_on_submit=True):
        user_input = st.text_input(f"{st.session_state.terminal.get_prompt()}", key="command_input")
        submit_button = st.form_submit_button(label="Execute")
        
        if submit_button and user_input:
            # Parse natural language if it doesn't look like a command
            if user_input and not user_input.split()[0] in st.session_state.terminal.commands:
                parsed_cmd = parse_natural_language(st.session_state.terminal, user_input)
                if parsed_cmd != user_input:
                    interpreted = f"Interpreted as: {parsed_cmd}"
                    user_input = parsed_cmd
                else:
                    interpreted = ""
            else:
                interpreted = ""
            
            # Execute the command
            result = st.session_state.terminal.execute(user_input)
            
            # Update output with styled command
            prompt = st.session_state.terminal.get_prompt()
            styled_prompt = f"<span class='terminal-input'>{prompt}</span>"
            
            # Apply syntax highlighting based on command type
            command_parts = user_input.split()
            if command_parts:
                cmd = command_parts[0]
                styled_cmd = f"<span class='terminal-command'>{cmd}</span>"
                
                # Style arguments (paths, etc)
                styled_args = ""
                if len(command_parts) > 1:
                    args = " ".join(command_parts[1:])
                    styled_args = f" <span class='terminal-path'>{args}</span>"
                
                styled_input = f"{styled_prompt}{styled_cmd}{styled_args}\n"
                new_output = styled_input
            if interpreted:
                new_output += f"{interpreted}\n"
            if result:
                new_output += f"{result}\n"
            
            st.session_state.output += new_output
            st.session_state.history.append(user_input)
            
            # Output will be displayed in the main terminal output area
            
            # Rerun to update the page
            st.rerun()
    
    # Help section
    with st.expander("Available Commands"):
        st.write("Basic Commands:")
        st.code("pwd - Print working directory\nls - List directory contents\ncd - Change directory\nmkdir - Create a directory\nrm - Remove files or directories\nhelp - Display help information\nmonitor - Display system monitoring information")
        
        st.write("Natural Language Examples:")
        st.code("create a folder called demo\nmove file1.txt into demo\ndelete all txt files\nwhere am I?\nlist all files")

# Update metrics every 5 seconds using Streamlit's native rerun mechanism
if st.checkbox("Auto-refresh metrics", value=True):
    update_metrics()
    # Use Streamlit's native rerun mechanism instead of meta refresh
    # This avoids the ScriptRunContext warnings
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    # Check if 5 seconds have passed since last refresh
    if time.time() - st.session_state.last_refresh > 5:
        st.session_state.last_refresh = time.time()
        st.rerun()