#!/bin/bash
# Install MCP Installer for macOS and Linux with embedded tools
# This version includes the mcp-collect-secret tool directly

set -e

# Configuration
GITHUB_USER="${GITHUB_USER:-ddfourtwo}"
GITHUB_REPO="install-mcp"
GITHUB_BRANCH="main"

echo "🚀 Installing Install MCP Server with tools..."
echo "   Repository: https://github.com/$GITHUB_USER/$GITHUB_REPO"
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p ~/mcp-servers/install-mcp
mkdir -p ~/.local/bin
cd ~/mcp-servers/install-mcp

# Download the server
echo "📥 Downloading Install MCP server..."
curl -sSL "https://raw.githubusercontent.com/$GITHUB_USER/$GITHUB_REPO/$GITHUB_BRANCH/server/meta_mcp_server.py" -o meta_mcp_server.py
curl -sSL "https://raw.githubusercontent.com/$GITHUB_USER/$GITHUB_REPO/$GITHUB_BRANCH/server/__main__.py" -o __main__.py
curl -sSL "https://raw.githubusercontent.com/$GITHUB_USER/$GITHUB_REPO/$GITHUB_BRANCH/server/web_secret_collector.py" -o web_secret_collector.py
curl -sSL "https://raw.githubusercontent.com/$GITHUB_USER/$GITHUB_REPO/$GITHUB_BRANCH/server/multi_secret_collector.py" -o multi_secret_collector.py

# Download requirements and pyproject.toml
curl -sSL "https://raw.githubusercontent.com/$GITHUB_USER/$GITHUB_REPO/$GITHUB_BRANCH/server/requirements.txt" -o requirements.txt
curl -sSL "https://raw.githubusercontent.com/$GITHUB_USER/$GITHUB_REPO/$GITHUB_BRANCH/server/pyproject.toml" -o pyproject.toml

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create an __init__.py file to make it a package
touch __init__.py

# Install the mcp-collect-secret tool directly (embedded in this script)
echo "📦 Installing mcp-collect-secret tool..."
cat > ~/.local/bin/mcp-collect-secret << 'COLLECT_SECRET_EOF'
#!/usr/bin/env python3
"""
MCP Secret Collector - Secure secret collection for MCP servers
Installed to ~/.local/bin/mcp-collect-secret
"""

import sys
import os
import json
import getpass
from pathlib import Path

def main():
    # Get arguments
    if len(sys.argv) != 4:
        print("Usage: mcp-collect-secret <server_name> <secret_name> <secret_description>")
        sys.exit(1)
    
    server_name = sys.argv[1]
    secret_name = sys.argv[2]
    secret_description = sys.argv[3]
    
    # Determine paths
    mcp_base_dir = Path.home() / "mcp-servers"
    server_dir = mcp_base_dir / server_name
    env_file = server_dir / ".env"
    
    print(f"🔐 Secure Secret Collection for {server_name}")
    print("=" * 50)
    print()
    print(f"This will collect: {secret_description}")
    print(f"Secret name: {secret_name}")
    print(f"Will be saved to: {env_file}")
    print()
    
    # Check if secret already exists
    existing_value = None
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    if line.strip().startswith(f"{secret_name}="):
                        existing_value = line.strip().split('=', 1)[1]
                        break
        except:
            pass
    
    if existing_value:
        print(f"⚠️  {secret_name} already exists in .env file")
        response = input("Do you want to update it? (y/N): ").strip().lower()
        if response != 'y':
            print("Keeping existing value.")
            sys.exit(0)
    
    # Collect the secret
    print()
    secret_value = getpass.getpass(f"Enter {secret_description}: ")
    
    if not secret_value:
        print("❌ No value entered. Exiting.")
        sys.exit(1)
    
    # Save to .env file
    try:
        server_dir.mkdir(parents=True, exist_ok=True)
        
        # Read existing content
        lines = []
        if env_file.exists():
            with open(env_file, 'r') as f:
                lines = f.readlines()
        
        # Update or append the secret
        found = False
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{secret_name}="):
                lines[i] = f"{secret_name}={secret_value}\n"
                found = True
                break
        
        if not found:
            lines.append(f"{secret_name}={secret_value}\n")
        
        # Write back
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        # Set restrictive permissions
        os.chmod(env_file, 0o600)
        
        print()
        print(f"✅ Secret saved to {env_file}")
        print("✨ Done! The secret has been securely saved.")
        
        # Return success for the MCP server
        print("STATUS:SUCCESS")
        
    except Exception as e:
        print(f"❌ Error saving secret: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
COLLECT_SECRET_EOF

chmod +x ~/.local/bin/mcp-collect-secret

# Install the configuration updater
echo "📦 Installing MCP configuration updater..."

# Download the Python script
curl -sSL "https://raw.githubusercontent.com/$GITHUB_USER/$GITHUB_REPO/$GITHUB_BRANCH/server/mcp_config_updater.py" -o ~/.local/bin/mcp_config_updater.py

# Download and install the wrapper script
curl -sSL "https://raw.githubusercontent.com/$GITHUB_USER/$GITHUB_REPO/$GITHUB_BRANCH/server/mcp-config-update" -o ~/.local/bin/mcp-config-update
chmod +x ~/.local/bin/mcp-config-update

# Add ~/.local/bin to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc 2>/dev/null || true
    export PATH="$HOME/.local/bin:$PATH"
fi

# Update MCP client configurations using the updater
echo "⚙️  Configuring MCP clients..."
# Try to use the updater if available, but don't fail if it has issues
(mcp-config-update install-mcp --command uv --args run --python 3.11 --with 'mcp>=1.0.0' --with 'fastmcp>=0.1.0' "$HOME/mcp-servers/install-mcp/meta_mcp_server.py" 2>/dev/null || \
 ~/.local/bin/mcp-config-update install-mcp --command uv --args run --python 3.11 --with 'mcp>=1.0.0' --with 'fastmcp>=0.1.0' "$HOME/mcp-servers/install-mcp/meta_mcp_server.py" 2>/dev/null || \
 true)

# Always run the direct Python configuration as backup
python3 - << 'PYEOF'
import json
import os
import shutil
from pathlib import Path

configs = {
    'claude_code': Path.home() / '.claude.json',
    'claude_desktop_mac': Path.home() / 'Library/Application Support/Claude/claude_desktop_config.json',
    'claude_desktop_linux': Path.home() / '.config/claude/claude_desktop_config.json',
    'cursor_mac': Path.home() / 'Library/Application Support/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json',
    'cursor_linux': Path.home() / '.config/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json',
    'windsurf': Path.home() / '.codeium/windsurf/mcp_config.json',
}

# Detect if uv is available
uv_cmd = shutil.which('uv')
if uv_cmd:
    # Use uv if available
    command = 'uv'
    args = ['run', '--python', '3.11', '--with', 'mcp>=1.0.0', '--with', 'fastmcp>=0.1.0', str(Path.home() / 'mcp-servers/install-mcp/meta_mcp_server.py')]
else:
    # Fallback to python3 if uv is not available
    print("⚠️  uv not found in PATH, using python3 directly")
    print("   For better dependency management, install uv: https://github.com/astral-sh/uv")
    command = 'python3'
    args = [str(Path.home() / 'mcp-servers/install-mcp/meta_mcp_server.py')]

updated = []
for name, path in configs.items():
    if path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        config = {}
        if path.exists():
            try:
                with open(path) as f:
                    config = json.load(f)
            except:
                print(f"⚠️  Could not read {name} config, creating new one")
        
        if 'mcpServers' not in config:
            config['mcpServers'] = {}
        
        config['mcpServers']['install-mcp'] = {
            'command': command,
            'args': args
        }
        
        try:
            with open(path, 'w') as f:
                json.dump(config, f, indent=2)
            updated.append(name)
            print(f'✅ Updated {name}')
        except Exception as e:
            print(f'⚠️  Could not update {name}: {e}')

if not updated:
    print("⚠️  No MCP clients found. Please install Claude Desktop, Cursor, or another MCP client.")
else:
    print(f"\n✅ Successfully configured: {', '.join(updated)}")
PYEOF

# Verify mcp-collect-secret was installed
if [ -x ~/.local/bin/mcp-collect-secret ]; then
    echo "✅ mcp-collect-secret tool installed successfully"
else
    echo "⚠️  Warning: mcp-collect-secret tool installation may have failed"
fi

echo ""
echo "✨ Install MCP installed successfully!"
echo ""
echo "The following tools are now available:"
echo "  - mcp-config-update: Update MCP client configurations"
echo "  - mcp-collect-secret: Securely collect API keys and secrets"
echo ""
echo "You may need to restart your terminal or run: source ~/.bashrc"
echo ""
echo "Next steps:"
echo "1. Restart your MCP client (Claude Desktop, Cursor, etc.)"
echo "2. Ask your AI: 'Can you test the install-mcp server?'"
echo "3. Then try: 'Install the GitHub MCP server for me'"
echo ""
echo "Documentation: https://github.com/$GITHUB_USER/$GITHUB_REPO"

# Optional: Run test
if [ -t 0 ]; then
    echo ""
    read -p "Would you like to test the installation? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Running installation test..."
        curl -sSL "https://raw.githubusercontent.com/$GITHUB_USER/$GITHUB_REPO/$GITHUB_BRANCH/test_meta_mcp.py" | python3
    fi
fi

# Ensure clean exit
exit 0
