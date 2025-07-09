#!/usr/bin/env python3
"""
Meta MCP Server for managing other MCP servers
"""

import json
import os
from pathlib import Path
import subprocess
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from fastmcp import FastMCP

# Create FastMCP server instance
mcp = FastMCP("install-mcp")

# Determine base directory for MCP servers
MCP_BASE_DIR = Path.home() / "mcp-servers"

# Central configuration file
MCP_CENTRAL_CONFIG = MCP_BASE_DIR / "mcp-servers-config.json"

# Central secrets file
MCP_CENTRAL_ENV = MCP_BASE_DIR / ".env"

# Configuration paths for different clients
MCP_CLIENT_CONFIGS = {
    "claude_desktop_macos": Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
    "claude_desktop_windows": Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json",
    "claude_desktop_linux": Path.home() / ".config" / "Claude" / "claude_desktop_config.json",
    "claude_code": Path.home() / ".claude.json",
    "cursor": Path.home() / ".cursor" / "User" / "globalStorage" / "cursor-ai.cursor-ai" / "config.json",
    "windsurf": Path.home() / ".codeium" / "windsurf" / "mcp_config.json"
}

def load_central_config() -> Dict[str, Any]:
    """Load the central MCP configuration file"""
    if MCP_CENTRAL_CONFIG.exists():
        try:
            with open(MCP_CENTRAL_CONFIG, 'r') as f:
                return json.load(f)
        except:
            pass
    
    # Return default structure
    return {
        "version": "1.0",
        "servers": {},
        "metadata": {
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
    }

def save_central_config(config: Dict[str, Any]) -> bool:
    """Save the central MCP configuration file"""
    try:
        # Update metadata
        config["metadata"]["last_updated"] = datetime.now().isoformat()
        
        # Ensure directory exists
        MCP_BASE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save with nice formatting
        with open(MCP_CENTRAL_CONFIG, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        return False

def load_central_env() -> Dict[str, str]:
    """Load the central .env file"""
    env_vars = {}
    if MCP_CENTRAL_ENV.exists():
        try:
            with open(MCP_CENTRAL_ENV, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        except:
            pass
    return env_vars

def save_to_central_env(key: str, value: str) -> bool:
    """Save a secret to the central .env file"""
    try:
        # Load existing env vars
        env_vars = load_central_env()
        
        # Update with new value
        env_vars[key] = value
        
        # Ensure directory exists
        MCP_BASE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Write back all env vars
        with open(MCP_CENTRAL_ENV, 'w') as f:
            for k, v in sorted(env_vars.items()):
                f.write(f"{k}={v}\n")
        
        # Set restrictive permissions
        os.chmod(MCP_CENTRAL_ENV, 0o600)
        return True
    except Exception as e:
        return False

def resolve_env_placeholders(config: Dict[str, Any], server_name: str = None) -> Dict[str, Any]:
    """Resolve .env placeholders in configuration"""
    import copy
    resolved_config = copy.deepcopy(config)
    
    # Load central env vars
    env_vars = load_central_env()
    
    # Check if there's an env section
    if 'env' in resolved_config:
        for key, value in resolved_config['env'].items():
            # Check if value is a placeholder (format: "KEY_NAME.env")
            if isinstance(value, str) and value.endswith('.env'):
                base_key = value[:-4]  # Remove .env suffix
                
                # Try namespaced key first (if server_name provided)
                if server_name:
                    namespaced_key = f"{server_name.upper().replace('-', '_')}_{base_key}"
                    if namespaced_key in env_vars:
                        resolved_config['env'][key] = env_vars[namespaced_key]
                        continue
                
                # Fallback to direct key
                if base_key in env_vars:
                    resolved_config['env'][key] = env_vars[base_key]
                # If not found, leave as is (will be empty string or cause error)
    
    return resolved_config

def get_server_config_template(server_name: str, command: str, args: List[str], 
                               required_env_vars: Optional[List[str]] = None) -> Dict[str, Any]:
    """Generate a server configuration template with placeholders for secrets"""
    config = {
        "command": command,
        "args": args
    }
    
    # If server requires environment variables, add placeholders
    if required_env_vars:
        config["env"] = {}
        for var in required_env_vars:
            # Use placeholder format: "VAR_NAME.env"
            config["env"][var] = f"{var}.env"
    
    return config

def generate_test_prompts(server_name: str, command: str, args: List[str]) -> List[str]:
    """Generate test prompts based on server name and type"""
    prompts = []
    
    # Check for specific server names or patterns
    server_lower = server_name.lower()
    
    # If it's an npm package, extract the package name
    if command == "npx" and args:
        for arg in args:
            if arg.startswith("@") and "/" in arg:
                # Extract package name like @upstash/context7-mcp
                package_parts = arg.split("@")[-1].split("/")[-1].split("-")[0]
                prompts.append(f"Test the {package_parts} tools from {server_name}")
                break
    
    # Generate prompts based on common server types
    if "context" in server_lower:
        prompts.extend([
            f"Use {server_name} to get documentation for Next.js",
            f"Test {server_name} by fetching React hooks documentation"
        ])
    elif "github" in server_lower:
        prompts.extend([
            f"Use {server_name} to list my recent repositories",
            f"Test {server_name} by checking my GitHub notifications"
        ])
    elif "slack" in server_lower:
        prompts.extend([
            f"Use {server_name} to list my Slack channels",
            f"Test {server_name} by checking recent messages"
        ])
    elif "file" in server_lower or "fs" in server_lower:
        prompts.extend([
            f"Use {server_name} to list files in my home directory",
            f"Test {server_name} file operations"
        ])
    elif "web" in server_lower or "browser" in server_lower:
        prompts.extend([
            f"Use {server_name} to fetch content from example.com",
            f"Test {server_name} web browsing capabilities"
        ])
    else:
        # Generic prompts
        prompts.extend([
            f"List all available tools from {server_name}",
            f"Test a few tools from {server_name} to ensure it's working"
        ])
    
    return prompts

def determine_installation_source(server_dir: Path) -> Dict[str, Any]:
    """Determine how a server was installed based on directory contents"""
    info = {}
    
    # Check for git repository
    if (server_dir / ".git").exists():
        try:
            # Get git remote URL
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=server_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                git_url = result.stdout.strip()
                info["installation_type"] = "git"
                info["source_url"] = git_url
        except:
            pass
    
    # Check for npm package
    if (server_dir / "package.json").exists():
        try:
            with open(server_dir / "package.json") as f:
                package_data = json.load(f)
                package_name = package_data.get("name")
                if package_name and package_name.startswith("@"):
                    info["installation_type"] = "npm"
                    info["npm_package"] = package_name
                    info["server_type"] = "node"
        except:
            pass
        
        if "installation_type" not in info:
            info["server_type"] = "node"
    
    # Check for Python server
    if (server_dir / "requirements.txt").exists() or (server_dir / "pyproject.toml").exists():
        info["server_type"] = "python"
        if (server_dir / "requirements.txt").exists():
            info["needs_requirements"] = True
    
    # Check for specific server patterns
    if (server_dir / ".env.example").exists():
        try:
            with open(server_dir / ".env.example") as f:
                env_content = f.read()
                # Extract required env vars
                import re
                env_vars = re.findall(r'^([A-Z_]+)=', env_content, re.MULTILINE)
                if env_vars:
                    info["required_secrets"] = env_vars
        except:
            pass
    
    return info

@mcp.tool()
def execute_in_mcp_directory(
    command: str,
    working_dir: Optional[str] = None,
    timeout: int = 300
) -> Dict[str, Any]:
    """
    Execute commands to install MCP servers. Use this after list_mcp_servers to install new servers.
    
    INSTALLATION PATTERNS BY SERVER TYPE:
    
    1. GitHub Node.js servers (has package.json):
       - Clone: execute_in_mcp_directory("git clone https://github.com/org/repo server-name", "")
       - Install: execute_in_mcp_directory("npm install", "server-name")
       - Build if needed: execute_in_mcp_directory("npm run build", "server-name")
       - Configure with: command="node", args=["dist/index.js"] or ["index.js"]
    
    2. GitHub Python servers (has requirements.txt):
       - Clone: execute_in_mcp_directory("git clone https://github.com/org/repo server-name", "")
       - Install: execute_in_mcp_directory("pip install -r requirements.txt", "server-name")
       - Configure with: command="python3", args=["server.py"] or ["main.py"]
    
    3. NPM packages (published to npm):
       - No installation needed!
       - Just configure with: command="npx", args=["-y", "@org/package-name@latest"]
    
    4. Check installation:
       - execute_in_mcp_directory("ls -la", "server-name")
       - execute_in_mcp_directory("cat package.json", "server-name") or README.md
    
    Args:
        command: Shell command to execute
        working_dir: Subdirectory within ~/mcp-servers/ (empty for base dir)
        timeout: Command timeout in seconds (default: 300)
    
    Returns:
        Dictionary with results. Check 'success' field and 'next_action' suggestion.
    
    WORKING_DIR TIPS:
    - For git clone: use working_dir="" and specify target in command
    - For other commands: use working_dir="server-name" to run inside that directory
    """
    # Ensure we're only operating within the MCP directory
    if working_dir:
        work_path = MCP_BASE_DIR / working_dir
        work_path.mkdir(parents=True, exist_ok=True)
    else:
        work_path = MCP_BASE_DIR
        work_path.mkdir(parents=True, exist_ok=True)
    
    # Log command to history file
    history_file = work_path / ".mcp_command_history.json"
    command_entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "working_dir": working_dir or ".",
        "cwd": str(work_path)
    }
    
    try:
        # Load existing history
        history = []
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
        
        # Append new command
        history.append(command_entry)
        
        # Save updated history
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        # Don't fail if history logging fails
        pass
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=work_path,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Update command entry with result
        command_entry["return_code"] = result.returncode
        command_entry["success"] = result.returncode == 0
        
        # Update history with result
        try:
            if history_file.exists():
                with open(history_file, 'r') as f:
                    history = json.load(f)
                if history and history[-1]["timestamp"] == command_entry["timestamp"]:
                    history[-1].update({
                        "return_code": result.returncode,
                        "success": result.returncode == 0
                    })
                    with open(history_file, 'w') as f:
                        json.dump(history, f, indent=2)
        except:
            pass
        
        # Determine next action based on command
        next_action = None
        if result.returncode == 0:
            if "git clone" in command:
                next_action = f"Next: Check what type of server this is with: execute_in_mcp_directory('ls -la', '{working_dir or command.split()[-1]}')"
            elif "npm install" in command and working_dir:
                next_action = f"Next: Check if build is needed with: execute_in_mcp_directory('cat package.json | grep scripts', '{working_dir}')"
            elif "npm run build" in command and working_dir:
                next_action = f"Next: Configure the server with: add_server_to_central_config('{working_dir}', 'node', '[\"/Users/username/mcp-servers/{working_dir}/build/index.js\"]')"
            elif "pip install" in command and working_dir:
                next_action = f"Next: Configure the server with: add_server_to_central_config('{working_dir}', 'python3', '[\"/Users/username/mcp-servers/{working_dir}/server.py\"]')"
            elif command in ["ls -la", "ls"] and result.stdout:
                if "package.json" in result.stdout:
                    next_action = f"Next: This is a Node.js server. Run: execute_in_mcp_directory('npm install', '{working_dir}')"
                elif "requirements.txt" in result.stdout:
                    next_action = f"Next: This is a Python server. Run: execute_in_mcp_directory('pip install -r requirements.txt', '{working_dir}')"
                elif "README" in result.stdout:
                    next_action = f"Next: Check the README for installation instructions: execute_in_mcp_directory('cat README.md', '{working_dir}')"
        
        response = {
            "command": command,
            "working_directory": str(work_path),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "success": result.returncode == 0
        }
        
        if next_action:
            response["next_action"] = next_action
            
        return response
    except subprocess.TimeoutExpired:
        return {
            "command": command,
            "working_directory": str(work_path),
            "error": f"Command timed out after {timeout} seconds",
            "success": False
        }
    except Exception as e:
        return {
            "command": command,
            "working_directory": str(work_path),
            "error": str(e),
            "success": False
        }

@mcp.tool()
def collect_secrets(
    server_name: str,
    secrets: str
) -> Dict[str, Any]:
    """
    Collect one or more API keys and secrets via secure web interface.
    
    This tool opens a local web server that:
    - Shows a secure form for entering secrets
    - Saves them to the central .env file with namespaced keys
    - Never exposes secret values in the MCP conversation
    
    Args:
        server_name: Name of the MCP server needing secrets (e.g., "github", "slack")
        secrets: JSON string containing either:
            - A single secret object: '{"name": "API_KEY", "description": "Your API Key"}'
            - An array of secret objects: '[{"name": "API_KEY", "description": "Your API Key"}, {"name": "API_SECRET", "description": "Your API Secret"}]'
    
    Returns:
        Dictionary with execution status (but never the secret values)
    
    Examples:
        # Single secret
        collect_secrets("github", '{"name": "GITHUB_TOKEN", "description": "GitHub Personal Access Token"}')
        
        # Multiple secrets
        collect_secrets("openai", '[{"name": "OPENAI_API_KEY", "description": "OpenAI API Key"}, {"name": "OPENAI_ORG_ID", "description": "OpenAI Organization ID"}]')
    """
    # Parse JSON string input
    try:
        secrets_parsed = json.loads(secrets)
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON in secrets parameter: {str(e)}",
            "hint": "Ensure secrets is valid JSON. For single secret: '{\"name\": \"KEY\", \"description\": \"desc\"}'. For multiple: '[{\"name\": \"KEY1\", \"description\": \"desc1\"}, {\"name\": \"KEY2\", \"description\": \"desc2\"}]'"
        }
    
    # Normalize input - convert single secret to list
    if isinstance(secrets_parsed, dict):
        secrets_list = [secrets_parsed]
    else:
        secrets_list = secrets_parsed
    
    # Build namespaced secrets for central .env file
    namespaced_secrets = []
    for secret in secrets_list:
        namespaced_key = f"{server_name.upper().replace('-', '_')}_{secret['name']}"
        namespaced_secrets.append({
            'name': namespaced_key,
            'description': secret['description'],
            'original_name': secret['name']
        })
    
    # Use multi-secret collector for all cases (works for single too)
    multi_collector_path = Path(__file__).parent / "multi_secret_collector.py"
    
    if multi_collector_path.exists():
        try:
            # Import and run the collector directly
            import importlib.util
            spec = importlib.util.spec_from_file_location("multi_secret_collector", multi_collector_path)
            multi_collector = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(multi_collector)
            
            # Run the multi-server function
            success = multi_collector.run_multi_server(server_name, namespaced_secrets, MCP_CENTRAL_ENV)
            
            if success:
                # Verify all secrets were saved
                central_env = load_central_env()
                saved_secrets = []
                missing_secrets = []
                
                for i, secret in enumerate(secrets_list):
                    namespaced_key = namespaced_secrets[i]['name']
                    if namespaced_key in central_env:
                        saved_secrets.append(secret['name'])
                    else:
                        missing_secrets.append(secret['name'])
                
                if saved_secrets and not missing_secrets:
                    return {
                        "success": True,
                        "status": "all_collected",
                        "message": f"✅ Successfully saved {len(saved_secrets)} secret{'s' if len(saved_secrets) != 1 else ''}",
                        "saved_secrets": saved_secrets,
                        "env_file": str(MCP_CENTRAL_ENV),
                        "next_steps": [
                            "All secrets have been saved and will be loaded when the server starts.",
                            "Use configure_mcp_clients(server_name) to update your MCP client configuration."
                        ]
                    }
                elif saved_secrets:
                    return {
                        "success": True,
                        "status": "partial_collection",
                        "message": f"✅ {len(saved_secrets)} of {len(secrets_list)} secrets saved",
                        "saved_secrets": saved_secrets,
                        "missing_secrets": missing_secrets,
                        "env_file": str(MCP_CENTRAL_ENV)
                    }
                else:
                    # Collection failed, provide manual instructions
                    return manual_secret_instructions(server_name, secrets_list, namespaced_secrets)
                    
        except Exception as e:
            import traceback
            return {
                "success": False,
                "status": "collector_error",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "fallback": manual_secret_instructions(server_name, secrets_list, namespaced_secrets)
            }
    
    # No collector available, provide manual instructions
    return manual_secret_instructions(server_name, secrets_list, namespaced_secrets)


def manual_secret_instructions(server_name: str, secrets_list: List[Dict[str, str]], namespaced_secrets: List[Dict[str, str]]) -> Dict[str, Any]:
    """Provide manual instructions for adding secrets"""
    instructions = [
        f"Please add these secrets manually to {MCP_CENTRAL_ENV}:",
        ""
    ]
    
    for i, secret in enumerate(secrets_list):
        namespaced_key = namespaced_secrets[i]['name']
        instructions.append(f"{i+1}. Add: {namespaced_key}=<your-{secret['name'].lower()}>")
    
    instructions.extend([
        "",
        "After adding all secrets, restart your MCP client to use them."
    ])
    
    return {
        "success": False,
        "status": "manual_required",
        "central_env_path": str(MCP_CENTRAL_ENV),
        "instructions": instructions
    }


@mcp.tool()
def configure_mcp_clients(
    server_name: str
) -> Dict[str, Any]:
    """
    Configure an MCP server in all clients from central configuration.
    
    This tool:
    - Reads server config from central mcp-servers-config.json
    - Resolves environment variables from central .env file
    - Updates all MCP client configurations
    - Creates backups before making changes
    
    Args:
        server_name: Name of the server to configure (must exist in central config)
    
    Returns:
        Configuration results with test prompts and next steps
    
    Example:
        configure_mcp_clients("sentry-selfhosted-mcp")
    """
    # Load central config
    central_config = load_central_config()
    
    if server_name not in central_config.get("servers", {}):
        return {
            "success": False,
            "error": f"Server '{server_name}' not found in central configuration",
            "available_servers": list(central_config.get("servers", {}).keys()),
            "hint": "First add the server to central config using execute_in_mcp_directory and collect_secrets"
        }
    
    server_info = central_config["servers"][server_name]
    server_config = server_info["config"]
    
    results = {
        "server_name": server_name,
        "updated_clients": [],
        "skipped_clients": [],
        "errors": []
    }
    
    # Update each client configuration
    for client_name, config_path in MCP_CLIENT_CONFIGS.items():
        if config_path.exists():
            try:
                # Backup existing config
                backup_path = config_path.with_suffix(f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
                
                # Read current config
                with open(config_path) as f:
                    config = json.load(f)
                
                # Create backup of original config
                with open(backup_path, 'w') as f:
                    json.dump(config, f, indent=2)
                
                # Ensure mcpServers section exists
                if 'mcpServers' not in config:
                    config['mcpServers'] = {}
                
                # Resolve placeholders and update server config
                resolved_config = resolve_env_placeholders(server_config, server_name)
                config['mcpServers'][server_name] = resolved_config
                
                # Write updated config
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                
                results["updated_clients"].append(f"{client_name} (backup: {backup_path.name})")
            except Exception as e:
                results["errors"].append(f"{client_name}: {str(e)}")
        else:
            results["skipped_clients"].append(f"{client_name} (not installed)")
    
    results["success"] = len(results["updated_clients"]) > 0
    if results["success"]:
        results["message"] = f"✅ Successfully configured {server_name} in {len(results['updated_clients'])} clients"
        
        # Add test prompts
        command = server_config.get("command", "")
        args = server_config.get("args", [])
        test_prompts = generate_test_prompts(server_name, command, args)
        results["test_prompts"] = test_prompts
        
        # Build next steps
        next_steps = [
            "1. Restart your MCP client (Claude Desktop, Cursor, Windsurf, etc.)",
            f"2. Test with one of these prompts:",
            *[f"   - {prompt}" for prompt in test_prompts],
            "3. Check if the server responds correctly"
        ]
        
        # Add note about env vars if any
        if server_info.get("required_env_vars"):
            next_steps.insert(0, f"Note: This server uses environment variables from {MCP_CENTRAL_ENV}")
        
        results["next_steps"] = next_steps
    else:
        results["message"] = f"❌ Failed to configure {server_name} in any clients"
    
    return results


@mcp.tool()
def add_server_to_central_config(
    server_name: str,
    command: str,
    args: str,
    required_env_vars: Optional[str] = None,
    env_vars: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a new MCP server to the central configuration.
    
    This saves the server configuration centrally. After adding, use
    configure_mcp_clients(server_name) to apply it to all clients.
    
    ENVIRONMENT VARIABLES:
    - Environment variables are stored as placeholders: "VAR_NAME.env"
    - These placeholders are resolved from the central .env file when configuring clients
    - Secrets are namespaced automatically: SERVERNAME_VAR_NAME
    - Example: For "github" server needing "TOKEN", it becomes GITHUB_TOKEN in .env
    
    IMPORTANT: Never pass actual secret values. Use collect_secrets() to securely collect them
    
    COMMAND FORMATS BY SERVER TYPE:
    
    1. NPM Package (from npm registry):
       add_server_to_central_config("server-name", "npx", '["-y", "@org/package@latest"]')
    
    2. Local Node.js server:
       add_server_to_central_config("server-name", "node", '["/Users/username/mcp-servers/server-name/index.js"]')
       
    3. Local Python server:
       add_server_to_central_config("server-name", "python3", '["/Users/username/mcp-servers/server-name/server.py"]')
    
    4. Pre-built executable:
       add_server_to_central_config("my-tool", "/path/to/executable", '[]')
    
    Args:
        server_name: Unique identifier for the server (lowercase, hyphens ok)
        command: The executable command (npx, node, python3, or full path)
        args: JSON array of arguments as a string (e.g., '["arg1", "arg2"]')
        required_env_vars: Optional JSON array of required environment variable names (e.g., '["API_KEY", "API_SECRET"]')
        env_vars: Optional JSON object of non-secret environment variables (e.g., '{"NODE_ENV": "production"}')
    
    Returns:
        Status with next steps for collecting secrets and configuring clients
    """
    # Parse JSON inputs
    try:
        args_parsed = json.loads(args)
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON in args parameter: {str(e)}",
            "hint": "Pass args as a JSON array string, e.g., '[\"path/to/server.js\"]'"
        }
    
    if required_env_vars is not None:
        try:
            required_env_vars_parsed = json.loads(required_env_vars)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON in required_env_vars parameter: {str(e)}",
                "hint": "Pass required_env_vars as a JSON array string, e.g., '[\"API_KEY\", \"API_SECRET\"]'"
            }
    else:
        required_env_vars_parsed = None
    
    if env_vars is not None:
        try:
            env_vars_parsed = json.loads(env_vars)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON in env_vars parameter: {str(e)}",
                "hint": "Pass env_vars as a JSON object string, e.g., '{\"NODE_ENV\": \"production\"}'"
            }
    else:
        env_vars_parsed = None
    
    results = {
        "server_name": server_name,
        "updated_clients": [],
        "skipped_clients": [],
        "errors": []
    }
    
    # Generate server configuration with placeholders for required env vars
    server_config = get_server_config_template(server_name, command, args_parsed, required_env_vars_parsed)
    
    # Add any additional env vars provided
    if env_vars_parsed:
        if "env" not in server_config:
            server_config["env"] = {}
        server_config["env"].update(env_vars_parsed)
    
    # Update central configuration
    central_config = load_central_config()
    central_config["servers"][server_name] = {
        "name": server_name,
        "config": server_config,
        "installed_at": datetime.now().isoformat(),
        "required_env_vars": required_env_vars_parsed or []
    }
    if not save_central_config(central_config):
        return {
            "success": False,
            "error": "Failed to save central configuration"
        }
    
    # Build result
    result = {
        "success": True,
        "message": f"✅ Added {server_name} to central configuration",
        "server_name": server_name,
        "central_config_path": str(MCP_CENTRAL_CONFIG),
        "config_saved": server_config
    }
    
    # Add next steps
    next_steps = []
    if required_env_vars_parsed:
        # Build the secrets JSON outside the f-string
        secrets_json = json.dumps([{"name": var, "description": f"{var} for {server_name}"} for var in required_env_vars_parsed])
        next_steps.append(f"1. Collect secrets: collect_secrets('{server_name}', '{secrets_json}')")
        next_steps.append(f"2. Configure clients: configure_mcp_clients('{server_name}')")
    else:
        next_steps.append(f"1. Configure clients: configure_mcp_clients('{server_name}')")
    
    result["next_steps"] = next_steps
    return result

@mcp.tool()
def sync_from_central_config() -> Dict[str, Any]:
    """
    Sync all MCP client configurations from the central config file.
    
    This tool reads the central mcp-servers-config.json and updates all MCP clients
    to match. Useful for:
    - Applying config changes across all clients at once
    - Restoring configurations after client updates
    - Setting up a new machine from an existing config
    
    Returns:
        Dictionary with sync results for each client
    """
    # Load central config
    central_config = load_central_config()
    
    if not central_config.get("servers"):
        return {
            "success": False,
            "message": "No servers found in central configuration",
            "config_path": str(MCP_CENTRAL_CONFIG)
        }
    
    results = {
        "synced_servers": [],
        "updated_clients": [],
        "errors": [],
        "central_config_path": str(MCP_CENTRAL_CONFIG)
    }
    
    # Update each client
    for client_name, config_path in MCP_CLIENT_CONFIGS.items():
        if config_path.exists():
            try:
                # Backup existing config
                backup_path = config_path.with_suffix(f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
                
                # Read current config
                with open(config_path) as f:
                    client_config = json.load(f)
                
                # Ensure mcpServers section exists
                if 'mcpServers' not in client_config:
                    client_config['mcpServers'] = {}
                
                # Update all servers from central config
                for server_name, server_info in central_config["servers"].items():
                    # Resolve environment placeholders before updating client config
                    resolved_config = resolve_env_placeholders(server_info["config"], server_name)
                    client_config['mcpServers'][server_name] = resolved_config
                    if server_name not in results["synced_servers"]:
                        results["synced_servers"].append(server_name)
                
                # Create backup
                with open(backup_path, 'w') as f:
                    json.dump(json.load(open(config_path)), f, indent=2)
                
                # Write updated config
                with open(config_path, 'w') as f:
                    json.dump(client_config, f, indent=2)
                
                results["updated_clients"].append(f"{client_name} (backup: {backup_path.name})")
            except Exception as e:
                results["errors"].append(f"{client_name}: {str(e)}")
    
    results["success"] = len(results["updated_clients"]) > 0
    if results["success"]:
        results["message"] = f"Synced {len(results['synced_servers'])} servers to {len(results['updated_clients'])} clients"
        results["next_steps"] = [
            "1. Restart your MCP clients to apply changes",
            "2. Test that servers are working correctly"
        ]
    else:
        results["message"] = "Failed to sync to any clients"
    
    return results

@mcp.tool()
def list_mcp_servers() -> Dict[str, Any]:
    """
    🚀 START HERE - List all installed MCP servers and check what needs to be installed.
    
    This tool shows you:
    - What MCP servers are already installed
    - Which ones are configured in MCP clients
    - Installation status and health
    
    Common MCP server types you'll encounter:
    - NPM packages (e.g., @upstash/context7-mcp) - use 'npx -y' command
    - GitHub repos with Node.js (package.json) - clone, npm install, use 'node' command
    - GitHub repos with Python (requirements.txt) - clone, pip install, use 'python3' command
    - Pre-built executables - download and run directly
    
    Always run this first to understand the current state before installing new servers.
    
    Returns:
        Dictionary containing server information, installation status, and suggestions
    """
    servers = []
    
    if MCP_BASE_DIR.exists():
        for server_dir in MCP_BASE_DIR.iterdir():
            if server_dir.is_dir() and server_dir.name != "install-mcp":
                server_info = {
                    "name": server_dir.name,
                    "path": str(server_dir),
                    "has_install_script": (server_dir / "install.sh").exists(),
                    "has_env_file": (server_dir / ".env").exists(),
                    "has_node_modules": (server_dir / "node_modules").exists(),
                    "has_package_json": (server_dir / "package.json").exists(),
                    "has_python_server": (server_dir / "server.py").exists(),
                    "files": len(list(server_dir.iterdir()))
                }
                
                # Check if installed in any client and get configuration
                installed_in = []
                server_config = None
                for client_name, config_path in MCP_CLIENT_CONFIGS.items():
                    if config_path.exists():
                        try:
                            with open(config_path) as f:
                                config = json.load(f)
                                if server_dir.name in config.get('mcpServers', {}):
                                    installed_in.append(client_name)
                                    if not server_config:
                                        server_config = config['mcpServers'][server_dir.name]
                        except:
                            pass
                
                server_info["configured_in_clients"] = installed_in
                server_info["is_configured"] = len(installed_in) > 0
                
                if server_config:
                    server_info["configuration"] = {
                        "command": server_config.get("command"),
                        "args": server_config.get("args", []),
                        "env": server_config.get("env", {})
                    }
                
                # Try to determine installation source
                installation_info = determine_installation_source(server_dir)
                server_info.update(installation_info)
                
                # Read command history if available
                history_file = server_dir / ".mcp_command_history.json"
                if history_file.exists():
                    try:
                        with open(history_file, 'r') as f:
                            command_history = json.load(f)
                            # Only include successful commands
                            successful_commands = [
                                cmd for cmd in command_history 
                                if cmd.get("success", True)  # Default to True for old entries
                            ]
                            server_info["installation_history"] = successful_commands
                            
                            # Extract key installation steps
                            installation_steps = []
                            for cmd in successful_commands:
                                command = cmd["command"]
                                if "git clone" in command:
                                    installation_steps.append(f"Cloned from: {command}")
                                elif "npm install" in command:
                                    installation_steps.append("Installed npm dependencies")
                                elif "npm run build" in command:
                                    installation_steps.append("Built with npm")
                                elif "pip install" in command:
                                    installation_steps.append("Installed Python dependencies")
                                elif command not in ["ls", "ls -la", "cat package.json"]:
                                    installation_steps.append(f"Ran: {command}")
                            
                            if installation_steps:
                                server_info["installation_steps"] = installation_steps
                    except Exception as e:
                        server_info["history_error"] = str(e)
                
                servers.append(server_info)
    
    # Add replication instructions if servers exist
    replication_instructions = []
    if servers:
        replication_instructions.append("To replicate this setup on another machine:")
        replication_instructions.append("1. Install the install-mcp server")
        replication_instructions.append("2. Use the information below to reinstall each server:")
        
        for server in servers:
            server_name = server['name']
            
            # If we have command history, use that for precise replication
            if server.get("installation_history"):
                replication_instructions.append(f"\n   {server_name}:")
                for step in server.get("installation_steps", []):
                    replication_instructions.append(f"      - {step}")
            elif server.get("installation_type") == "npm" and server.get("npm_package"):
                # NPM packages don't need installation, just configuration
                replication_instructions.append(f"\n   {server_name}: No installation needed, just configure")
            elif server.get("installation_type") == "git" and server.get("source_url"):
                replication_instructions.append(f"\n   {server_name}: Clone from {server['source_url']}")
            else:
                replication_instructions.append(f"\n   {server_name}: Check configuration details below")
    
    # Check central config status
    central_config = load_central_config()
    central_config_status = {
        "exists": MCP_CENTRAL_CONFIG.exists(),
        "path": str(MCP_CENTRAL_CONFIG),
        "servers_in_config": len(central_config.get("servers", {})),
        "last_updated": central_config.get("metadata", {}).get("last_updated", "never")
    }
    
    return {
        "base_directory": str(MCP_BASE_DIR),
        "total_servers": len(servers),
        "servers": servers,
        "central_config": central_config_status,
        "replication_instructions": replication_instructions if servers else ["No servers installed yet"]
    }

@mcp.tool()
def export_mcp_setup() -> Dict[str, Any]:
    """
    Export complete MCP setup for sharing or replication.
    
    This tool gathers all information needed to replicate your exact MCP setup
    on another machine, including:
    - Installed servers and their configurations
    - Installation commands from history
    - Required environment variables (without exposing secrets)
    - Step-by-step replication instructions
    
    Use this when you want to:
    - Share your MCP setup with others
    - Document your configuration
    - Set up MCP on a new machine
    - Create a backup of your setup
    
    Returns:
        Complete setup information with replication instructions
    """
    setup_info = {
        "export_timestamp": datetime.now().isoformat(),
        "mcp_base_directory": str(MCP_BASE_DIR),
        "servers": [],
        "central_config_path": str(MCP_CENTRAL_CONFIG),
        "central_env_path": str(MCP_CENTRAL_ENV)
    }
    
    # Load central config
    central_config = load_central_config()
    
    # Get list of installed servers
    servers_data = []
    if MCP_BASE_DIR.exists():
        for server_dir in MCP_BASE_DIR.iterdir():
            if server_dir.is_dir() and server_dir.name != "install-mcp":
                server_info = {
                    "name": server_dir.name,
                    "directory": str(server_dir),
                    "installation_commands": [],
                    "configuration": {},
                    "required_secrets": []
                }
                
                # Get configuration from central config
                if server_dir.name in central_config.get("servers", {}):
                    server_central = central_config["servers"][server_dir.name]
                    server_info["configuration"] = server_central.get("config", {})
                    server_info["required_secrets"] = server_central.get("required_env_vars", [])
                
                # Get installation history
                history_file = server_dir / ".mcp_command_history.json"
                if history_file.exists():
                    try:
                        with open(history_file, 'r') as f:
                            command_history = json.load(f)
                            # Only include successful commands
                            successful_commands = [
                                cmd["command"] for cmd in command_history 
                                if cmd.get("success", True) and cmd["command"] not in ["ls", "ls -la", "pwd"]
                            ]
                            server_info["installation_commands"] = successful_commands
                    except:
                        pass
                
                # Determine installation type
                if (server_dir / ".git").exists():
                    try:
                        result = subprocess.run(
                            ["git", "remote", "get-url", "origin"],
                            cwd=server_dir,
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            server_info["git_url"] = result.stdout.strip()
                    except:
                        pass
                
                servers_data.append(server_info)
    
    setup_info["servers"] = servers_data
    
    # Build replication instructions
    instructions = [
        "# MCP Setup Replication Instructions",
        "",
        "## Prerequisites",
        "1. Install Claude Desktop, Cursor, or another MCP-compatible client",
        "2. Install the install-mcp server:",
        "   - For Claude Desktop: Add to config manually or use an existing install-mcp",
        "   - Command: `uv tool install --from ../../path/to/install-mcp/server install-mcp`",
        "",
        "## Automated Installation Steps",
        ""
    ]
    
    # Add installation commands for each server
    for i, server in enumerate(servers_data, 1):
        instructions.append(f"### {i}. {server['name']}")
        
        # Installation commands
        if server.get("git_url"):
            instructions.append(f"```bash")
            instructions.append(f"# Clone the repository")
            instructions.append(f"execute_in_mcp_directory('git clone {server['git_url']} {server['name']}', '')")
            
            # Add other installation commands
            for cmd in server['installation_commands']:
                if "git clone" not in cmd:  # Skip git clone as we already have it
                    instructions.append(f"execute_in_mcp_directory('{cmd}', '{server['name']}')")
            instructions.append("```")
        elif server['installation_commands']:
            instructions.append("```bash")
            for cmd in server['installation_commands']:
                instructions.append(f"execute_in_mcp_directory('{cmd}', '{server['name']}')")
            instructions.append("```")
        
        # Configuration command
        config = server['configuration']
        if config:
            command = config.get('command', '')
            args = config.get('args', [])
            required_vars = server['required_secrets']
            
            instructions.append("")
            instructions.append("# Add to central config")
            if required_vars:
                instructions.append(f"add_server_to_central_config('{server['name']}', '{command}', '{json.dumps(args)}', '{json.dumps(required_vars)}')")
                instructions.append("")
                instructions.append("# Collect secrets")
                secrets_list = [{"name": var, "description": f"{var} for {server['name']}"} for var in required_vars]
                instructions.append(f"collect_secrets('{server['name']}', '{json.dumps(secrets_list)}')")
            else:
                instructions.append(f"add_server_to_central_config('{server['name']}', '{command}', '{json.dumps(args)}')")
        
        instructions.append("")
    
    # Final configuration step
    instructions.append("## Final Step: Configure All Clients")
    instructions.append("```bash")
    for server in servers_data:
        instructions.append(f"configure_mcp_clients('{server['name']}')")
    instructions.append("```")
    
    # Add manual configuration section
    instructions.append("")
    instructions.append("## Manual Configuration (if needed)")
    instructions.append("")
    instructions.append("If automated installation fails, here are the manual configurations:")
    instructions.append("")
    
    for server in servers_data:
        if server['configuration']:
            instructions.append(f"### {server['name']}")
            instructions.append("```json")
            instructions.append(json.dumps({server['name']: server['configuration']}, indent=2))
            instructions.append("```")
            if server['required_secrets']:
                instructions.append(f"Required environment variables: {', '.join(server['required_secrets'])}")
            instructions.append("")
    
    # Build final result
    result = {
        "success": True,
        "message": "✅ Successfully exported MCP setup",
        "total_servers": len(servers_data),
        "setup_info": setup_info,
        "replication_instructions": "\n".join(instructions),
        "notes": [
            "The instructions above will replicate your exact MCP setup",
            "Secrets are not exported - they must be re-entered on the new machine",
            "Save these instructions to share your setup or for future reference"
        ]
    }
    
    return result

def main():
    """Main entry point for the server"""
    mcp.run()

# Run the server
if __name__ == "__main__":
    main()