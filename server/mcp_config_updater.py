#!/usr/bin/env python3
"""
MCP Configuration Updater
A reusable utility for updating MCP client configurations
Installed with Install MCP and used by all MCP server installations
"""

import json
import sys
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
from datetime import datetime

# MCP client configuration paths
MCP_CLIENT_CONFIGS = {
    "claude_code": Path.home() / ".claude.json",
    "claude_desktop_mac": Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",
    "claude_desktop_linux": Path.home() / ".config/claude/claude_desktop_config.json",
    "claude_desktop_windows": Path.home() / "AppData/Roaming/Claude/claude_desktop_config.json",
    "cursor_mac": Path.home() / "Library/Application Support/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
    "cursor_linux": Path.home() / ".config/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
    "cursor_windows": Path.home() / "AppData/Roaming/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
    "windsurf_mac": Path.home() / ".windsurf/mcp.json",
    "windsurf_windows": Path.home() / ".windsurf/mcp.json",
    "windsurf_linux": Path.home() / ".windsurf/mcp.json",
}

def backup_config(config_path: Path) -> Optional[Path]:
    """
    Create a backup of the configuration file
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Path to the backup file or None if backup failed
    """
    if not config_path.exists():
        return None
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config_path.with_suffix(f".backup_{timestamp}.json")
    
    try:
        shutil.copy2(config_path, backup_path)
        return backup_path
    except Exception:
        return None

def validate_server_name(name: str) -> bool:
    """Validate server name follows conventions"""
    if not name:
        return False
    # Allow alphanumeric, hyphens, underscores
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))

def detect_command_and_args(server_dir: Path) -> tuple[str, List[str]]:
    """
    Automatically detect the command and arguments based on server type
    
    Args:
        server_dir: Path to the server directory
        
    Returns:
        Tuple of (command, args)
    """
    # Try to import the uv_detector module if available
    try:
        import sys
        # Add the server directory to path temporarily
        sys.path.insert(0, str(Path(__file__).parent))
        from uv_detector import get_portable_mcp_command
        # Use the portable command detector
        return get_portable_mcp_command(server_dir.name, server_dir)
    except ImportError:
        # Fallback to original detection logic
        pass
    finally:
        # Clean up sys.path
        if str(Path(__file__).parent) in sys.path:
            sys.path.remove(str(Path(__file__).parent))
    
    # Original detection logic as fallback
    # Check for TypeScript/JavaScript servers
    if (server_dir / "package.json").exists():
        if (server_dir / "build" / "index.js").exists():
            return "node", [str(server_dir / "build" / "index.js")]
        elif (server_dir / "dist" / "index.js").exists():
            return "node", [str(server_dir / "dist" / "index.js")]
        elif (server_dir / "index.js").exists():
            return "node", [str(server_dir / "index.js")]
        else:
            # Default for npm packages
            return "npx", ["-y", server_dir.name]
    
    # Check for Python servers with pyproject.toml
    elif (server_dir / "pyproject.toml").exists():
        # For install-mcp, prefer python -m for portability
        if server_dir.name == "install-mcp" and (server_dir / "__main__.py").exists():
            return "python3", ["-m", "install_mcp"]
        # For other pyproject.toml servers, use uv if available
        elif shutil.which("uv"):
            if (server_dir / "meta_mcp_server.py").exists():
                return "uv", ["run", "--python", "3.11", str(server_dir / "meta_mcp_server.py")]
            elif (server_dir / "server.py").exists():
                return "uv", ["run", "--python", "3.11", str(server_dir / "server.py")]
        # Fallback to python3
        elif (server_dir / "server.py").exists():
            return "python3", [str(server_dir / "server.py")]
    
    # Check for traditional Python servers
    elif (server_dir / "server.py").exists():
        return "python3", [str(server_dir / "server.py")]
    elif (server_dir / "__main__.py").exists():
        return "python3", ["-m", server_dir.name.replace("-", "_")]
    elif (server_dir / (server_dir.name.replace("-", "_") + ".py")).exists():
        return "python3", [str(server_dir / (server_dir.name.replace("-", "_") + ".py"))]
    
    # Check for shell scripts
    elif (server_dir / "server.sh").exists():
        return "bash", [str(server_dir / "server.sh")]
    
    # Check for binary executables
    elif (server_dir / server_dir.name).exists() and os.access(server_dir / server_dir.name, os.X_OK):
        return str(server_dir / server_dir.name), []
    
    # Default fallback
    else:
        return "node", [str(server_dir / "index.js")]

def update_config(
    server_name: str,
    command: Optional[str] = None,
    args: Optional[List[str]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    server_path: Optional[str] = None,
    remove: bool = False,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Update all MCP client configurations for a server
    
    Args:
        server_name: Name of the MCP server
        command: Command to run the server (auto-detected if not provided)
        args: Arguments for the command (auto-detected if not provided)
        env_vars: Environment variables to set
        server_path: Path to server directory (defaults to ~/mcp-servers/{server_name})
        remove: If True, remove the server from configurations
        verbose: If True, print status messages
        
    Returns:
        Dictionary with update results
    """
    results = {
        "updated": [],
        "skipped": [],
        "errors": [],
        "total_clients": 0
    }
    
    # Validate server name
    if not validate_server_name(server_name):
        raise ValueError(f"Invalid server name: {server_name}. Use only alphanumeric characters, hyphens, and underscores.")
    
    # Determine server path
    if server_path:
        server_dir = Path(server_path)
    else:
        server_dir = Path.home() / "mcp-servers" / server_name
    
    # Auto-detect command and args if not provided
    if not remove and not command:
        command, detected_args = detect_command_and_args(server_dir)
        if not args:
            args = detected_args
    
    # Process each client configuration
    for client_name, config_path in MCP_CLIENT_CONFIGS.items():
        # Skip non-existent paths
        if not config_path.parent.exists():
            results["skipped"].append(f"{client_name} (directory not found)")
            continue
            
        try:
            # Ensure parent directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read existing config or create new
            config = {}
            if config_path.exists():
                # Create backup before modifying
                backup_path = backup_config(config_path)
                if backup_path and verbose:
                    print(f"   💾 Backup created: {backup_path.name}")
                    
                with open(config_path, 'r') as f:
                    config = json.load(f)
            
            # Initialize mcpServers if needed
            if 'mcpServers' not in config:
                config['mcpServers'] = {}
            
            if remove:
                # Remove server
                if server_name in config['mcpServers']:
                    del config['mcpServers'][server_name]
                    action = "removed from"
                else:
                    results["skipped"].append(f"{client_name} (not configured)")
                    continue
            else:
                # Add/update server
                server_config = {
                    'command': command,
                    'args': args or []
                }
                
                # Add environment variables if provided
                if env_vars:
                    server_config['env'] = env_vars
                
                # Check if .env file exists and add NODE_ENV if it's a Node server
                if (server_dir / ".env").exists() and command in ["node", "npx"]:
                    if 'env' not in server_config:
                        server_config['env'] = {}
                    server_config['env']['NODE_ENV'] = 'production'
                
                config['mcpServers'][server_name] = server_config
                action = "added to" if server_name not in config['mcpServers'] else "updated in"
            
            # Write updated config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            results["updated"].append(f"{client_name} ({action})")
            results["total_clients"] += 1
            
        except json.JSONDecodeError as e:
            results["errors"].append(f"{client_name}: Invalid JSON - {str(e)}")
        except PermissionError:
            results["errors"].append(f"{client_name}: Permission denied")
        except Exception as e:
            results["errors"].append(f"{client_name}: {str(e)}")
    
    # Print results if verbose
    if verbose:
        print(f"\n{'Removing' if remove else 'Configuring'} {server_name} MCP server...")
        
        if results["updated"]:
            print(f"✅ Updated {len(results['updated'])} clients:")
            for client in results["updated"]:
                print(f"   - {client}")
        
        if results["skipped"]:
            print(f"⏭️  Skipped {len(results['skipped'])} clients:")
            for client in results["skipped"]:
                print(f"   - {client}")
        
        if results["errors"]:
            print(f"❌ Errors in {len(results['errors'])} clients:")
            for error in results["errors"]:
                print(f"   - {error}")
        
        if not results["updated"] and not remove:
            print("⚠️  No MCP clients found. Please install Claude Desktop, Cursor, or another MCP client.")
    
    return results

def list_configured_servers(verbose: bool = True) -> Dict[str, List[str]]:
    """
    List all configured MCP servers across all clients
    
    Args:
        verbose: If True, print the list
        
    Returns:
        Dictionary mapping server names to list of clients
    """
    all_servers = {}
    
    for client_name, config_path in MCP_CLIENT_CONFIGS.items():
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    
                servers = config.get('mcpServers', {})
                for server_name in servers:
                    if server_name not in all_servers:
                        all_servers[server_name] = []
                    all_servers[server_name].append(client_name)
            except json.JSONDecodeError:
                if verbose:
                    print(f"⚠️  Warning: Invalid JSON in {client_name} config")
            except Exception as e:
                if verbose:
                    print(f"⚠️  Warning: Could not read {client_name} config: {e}")
    
    if verbose and all_servers:
        print("\n📋 Configured MCP Servers:")
        for server_name, clients in sorted(all_servers.items()):
            print(f"\n{server_name}:")
            for client in clients:
                print(f"  - {client}")
    
    return all_servers

def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description='MCP Configuration Updater - Manage MCP server configurations across all clients',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add/update a server (auto-detect command)
  mcp-config-update my-server
  
  # Add/update with specific command
  mcp-config-update my-server --command python3 --args /path/to/server.py
  
  # Remove a server
  mcp-config-update my-server --remove
  
  # List all configured servers
  mcp-config-update --list
  
  # Add with environment variables
  mcp-config-update my-server --env API_KEY=secret TOKEN=xyz
        """
    )
    
    parser.add_argument('server_name', nargs='?', help='Name of the MCP server')
    parser.add_argument('--command', '-c', help='Command to run the server')
    parser.add_argument('--args', '-a', nargs='+', help='Arguments for the command')
    parser.add_argument('--env', '-e', action='append', help='Environment variables (KEY=VALUE format)')
    parser.add_argument('--path', '-p', help='Path to server directory')
    parser.add_argument('--remove', '-r', action='store_true', help='Remove server from configurations')
    parser.add_argument('--list', '-l', action='store_true', help='List all configured servers')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress output')
    
    args = parser.parse_args()
    
    # List mode
    if args.list:
        list_configured_servers(verbose=not args.quiet)
        return 0
    
    # Validate arguments
    if not args.server_name:
        parser.error("server_name is required unless using --list")
    
    # Parse environment variables
    env_vars = {}
    if args.env:
        for env_pair in args.env:
            if '=' not in env_pair:
                parser.error(f"Invalid environment variable format: {env_pair} (expected KEY=VALUE)")
            key, value = env_pair.split('=', 1)
            env_vars[key] = value
    
    # Update configurations
    results = update_config(
        server_name=args.server_name,
        command=args.command,
        args=args.args,
        env_vars=env_vars if env_vars else None,
        server_path=args.path,
        remove=args.remove,
        verbose=not args.quiet
    )
    
    # Return appropriate exit code
    if results["errors"]:
        return 1
    elif not results["updated"] and not args.remove:
        return 2
    else:
        return 0

if __name__ == "__main__":
    sys.exit(main())
