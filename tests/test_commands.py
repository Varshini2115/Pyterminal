import os
import shutil
import pytest
from terminal.core import Terminal
from terminal.commands import pwd, ls, cd, mkdir, rm

@pytest.fixture
def terminal():
    """Create a terminal instance for testing"""
    term = Terminal()
    term.register_command("pwd", pwd, "Print working directory")
    term.register_command("ls", ls, "List directory contents")
    term.register_command("cd", cd, "Change directory")
    term.register_command("mkdir", mkdir, "Create a directory")
    term.register_command("rm", rm, "Remove files or directories")
    return term

@pytest.fixture
def test_dir(tmp_path):
    """Create a temporary directory for testing"""
    return tmp_path

def test_pwd(terminal):
    """Test pwd command"""
    result = terminal.execute("pwd")
    assert result == terminal.current_dir

def test_mkdir_and_ls(terminal, test_dir):
    """Test mkdir and ls commands"""
    # Change to test directory
    terminal.current_dir = str(test_dir)
    
    # Create a test directory
    result = terminal.execute("mkdir testdir")
    assert "Directory created" in result
    assert os.path.isdir(os.path.join(test_dir, "testdir"))
    
    # List directory contents
    result = terminal.execute("ls")
    assert "testdir" in result

def test_cd(terminal, test_dir):
    """Test cd command"""
    # Change to test directory
    terminal.current_dir = str(test_dir)
    
    # Create a test directory
    os.makedirs(os.path.join(test_dir, "testdir"))
    
    # Change to the test directory
    result = terminal.execute("cd testdir")
    assert result == ""
    assert terminal.current_dir.endswith("testdir")
    
    # Change back to parent directory
    result = terminal.execute("cd ..")
    assert result == ""
    assert terminal.current_dir == str(test_dir)

def test_rm(terminal, test_dir):
    """Test rm command"""
    # Change to test directory
    terminal.current_dir = str(test_dir)
    
    # Create a test directory and file
    os.makedirs(os.path.join(test_dir, "testdir"))
    with open(os.path.join(test_dir, "testfile.txt"), "w") as f:
        f.write("test content")
    
    # Remove the file
    result = terminal.execute("rm testfile.txt")
    assert "File removed" in result
    assert not os.path.exists(os.path.join(test_dir, "testfile.txt"))
    
    # Try to remove directory without -r
    result = terminal.execute("rm testdir")
    assert "Error" in result
    assert os.path.exists(os.path.join(test_dir, "testdir"))
    
    # Remove directory with -r
    result = terminal.execute("rm -r testdir")
    assert "Directory removed" in result
    assert not os.path.exists(os.path.join(test_dir, "testdir"))