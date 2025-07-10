#!/usr/bin/env python3
"""
UV Command Detector and Portable Path Resolution

This module provides portable detection and execution of the uv command
across different platforms and installation methods.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple, List
import shutil


def find_uv_command() -> Optional[str]:
    """
    Find the uv command in various locations.
    
    Returns:
        The path to uv command or None if not found
    """
    # Method 1: Check if uv is in PATH using shutil.which (most portable)
    uv_path = shutil.which("uv")
    if uv_path:
        return uv_path
    
    # Method 2: Check common installation locations
    common_locations = [
        Path.home() / ".local" / "bin" / "uv",
        Path.home() / ".cargo" / "bin" / "uv",
        Path("/usr/local/bin/uv"),
        Path("/opt/homebrew/bin/uv"),
        Path("/usr/bin/uv"),
    ]
    
    # Add Windows-specific locations
    if sys.platform == "win32":
        common_locations.extend([
            Path.home() / "AppData" / "Local" / "Programs" / "uv" / "uv.exe",
            Path("C:/Program Files/uv/uv.exe"),
            Path.home() / ".cargo" / "bin" / "uv.exe",
        ])
    
    for location in common_locations:
        if location.exists() and os.access(location, os.X_OK):
            return str(location)
    
    # Method 3: Try to find uv using system commands
    if sys.platform != "win32":
        try:
            # Try command -v (POSIX compatible)
            result = subprocess.run(
                ["command", "-v", "uv"],
                capture_output=True,
                text=True,
                shell=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except:
            pass
        
        try:
            # Try which (less portable but widely available)
            result = subprocess.run(
                ["which", "uv"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except:
            pass
    
    return None


def verify_uv_command(uv_path: str) -> bool:
    """
    Verify that the uv command works correctly.
    
    Args:
        uv_path: Path to the uv command
        
    Returns:
        True if uv command works, False otherwise
    """
    try:
        result = subprocess.run(
            [uv_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0 and "uv" in result.stdout.lower()
    except:
        return False


def get_uv_run_command(script_path: str, use_python_fallback: bool = True) -> Tuple[str, List[str]]:
    """
    Get the appropriate command to run a Python script with uv.
    
    Args:
        script_path: Path to the Python script to run
        use_python_fallback: Whether to fall back to python3 if uv not found
        
    Returns:
        Tuple of (command, args) to execute
    """
    # Try to find uv
    uv_path = find_uv_command()
    
    if uv_path and verify_uv_command(uv_path):
        # Use uv run with proper arguments
        return uv_path, ["run", "--python", "3.11", script_path]
    
    # Check if we can use uvx (for installed packages)
    uvx_path = shutil.which("uvx")
    if uvx_path:
        try:
            result = subprocess.run(
                [uvx_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # If this is a package that can be run with uvx, return that
                # Note: This would need package name detection logic
                pass
        except:
            pass
    
    # Fallback options
    if use_python_fallback:
        # Try python3
        python3_path = shutil.which("python3")
        if python3_path:
            return python3_path, [script_path]
        
        # Try python
        python_path = shutil.which("python")
        if python_path:
            return python_path, [script_path]
    
    # If all else fails, return "uv" and hope it's in PATH when executed
    return "uv", ["run", "--python", "3.11", script_path]


def get_portable_mcp_command(server_name: str, server_path: Path) -> Tuple[str, List[str]]:
    """
    Get a portable command configuration for an MCP server.
    
    Args:
        server_name: Name of the MCP server
        server_path: Path to the server directory
        
    Returns:
        Tuple of (command, args) for MCP configuration
    """
    # Special case for install-mcp using pyproject.toml
    if server_name == "install-mcp" and (server_path / "pyproject.toml").exists():
        # Try different execution methods in order of preference
        
        # Method 1: Try uv tool run (if installed as a tool)
        if shutil.which("uv"):
            # Check if installed as a uv tool
            try:
                result = subprocess.run(
                    ["uv", "tool", "list"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and "install-mcp" in result.stdout:
                    return "uv", ["tool", "run", "install-mcp"]
            except:
                pass
        
        # Method 2: Try uvx (for package execution)
        if shutil.which("uvx"):
            return "uvx", ["install-mcp"]
        
        # Method 3: Use python -m with the module
        if (server_path / "__main__.py").exists():
            # This approach is more portable as it doesn't rely on uv
            return "python3", ["-m", "install_mcp"]
        
        # Method 4: Direct script execution with uv run
        main_script = server_path / "meta_mcp_server.py"
        if main_script.exists():
            command, args = get_uv_run_command(str(main_script))
            return command, args
    
    # For other Python servers
    if (server_path / "pyproject.toml").exists() or (server_path / "requirements.txt").exists():
        # Look for main entry points
        for entry_point in ["server.py", "__main__.py", f"{server_name.replace('-', '_')}.py"]:
            script_path = server_path / entry_point
            if script_path.exists():
                command, args = get_uv_run_command(str(script_path))
                return command, args
    
    # For Node.js servers
    if (server_path / "package.json").exists():
        # Check for built files
        for built_path in ["dist/index.js", "build/index.js", "index.js"]:
            if (server_path / built_path).exists():
                return "node", [str(server_path / built_path)]
        
        # For npm packages, use npx
        return "npx", ["-y", server_name]
    
    # Default fallback
    return "python3", [str(server_path / "server.py")]


def install_uv_if_needed() -> bool:
    """
    Check if uv is installed and install it if needed.
    
    Returns:
        True if uv is available (already installed or successfully installed)
    """
    # Check if uv is already available
    if find_uv_command():
        return True
    
    print("📦 UV is not installed. Installing now...")
    
    try:
        # Download and run the official installer
        if sys.platform == "win32":
            # Windows: Use PowerShell
            subprocess.run([
                "powershell", "-c",
                "irm https://astral.sh/uv/install.ps1 | iex"
            ], check=True)
        else:
            # Unix-like: Use curl
            subprocess.run([
                "sh", "-c",
                "curl -LsSf https://astral.sh/uv/install.sh | sh"
            ], check=True)
        
        # Add to PATH for current session
        if sys.platform != "win32":
            os.environ["PATH"] = f"{Path.home() / '.cargo' / 'bin'}:{os.environ.get('PATH', '')}"
        
        # Verify installation
        return find_uv_command() is not None
        
    except subprocess.CalledProcessError:
        print("❌ Failed to install UV automatically.")
        print("Please install UV manually from: https://github.com/astral-sh/uv")
        return False
    except Exception as e:
        print(f"❌ Error installing UV: {e}")
        return False


if __name__ == "__main__":
    # Test the detector
    print("🔍 Detecting UV installation...")
    
    uv_path = find_uv_command()
    if uv_path:
        print(f"✅ Found UV at: {uv_path}")
        if verify_uv_command(uv_path):
            print("✅ UV command verified and working")
        else:
            print("❌ UV command found but not working properly")
    else:
        print("❌ UV not found in PATH or common locations")
        if install_uv_if_needed():
            print("✅ UV installed successfully")
        else:
            print("❌ Could not install UV")
    
    # Test portable command generation
    print("\n🔧 Testing portable command generation:")
    test_path = Path.home() / "mcp-servers" / "install-mcp"
    command, args = get_portable_mcp_command("install-mcp", test_path)
    print(f"Command: {command}")
    print(f"Args: {args}")