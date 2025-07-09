# Install MCP Installer for Windows with embedded tools
# This version includes the mcp-collect-secret tool directly

# Configuration
$githubUser = if ($env:GITHUB_USER) { $env:GITHUB_USER } else { "ddfourtwo" }
$githubRepo = "install-mcp"
$githubBranch = "main"

Write-Host "🚀 Installing Install MCP Server..." -ForegroundColor Cyan
Write-Host "   Repository: https://github.com/$githubUser/$githubRepo" -ForegroundColor Gray
Write-Host ""

# Check for Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python 3 is required but not installed." -ForegroundColor Red
    Write-Host "Please install Python 3 from python.org and try again."
    exit 1
}

# Create directory structure
Write-Host "📁 Creating directory structure..." -ForegroundColor Yellow
$mcpPath = "$env:USERPROFILE\mcp-servers\install-mcp"
New-Item -ItemType Directory -Force -Path $mcpPath | Out-Null
Set-Location $mcpPath

# Download the server
Write-Host "📥 Downloading Install MCP server..." -ForegroundColor Yellow
$serverUrl = "https://raw.githubusercontent.com/$githubUser/$githubRepo/$githubBranch/server/meta_mcp_server.py"
$requirementsUrl = "https://raw.githubusercontent.com/$githubUser/$githubRepo/$githubBranch/server/requirements.txt"
$pyprojectUrl = "https://raw.githubusercontent.com/$githubUser/$githubRepo/$githubBranch/server/pyproject.toml"
$mainUrl = "https://raw.githubusercontent.com/$githubUser/$githubRepo/$githubBranch/server/__main__.py"
$webSecretUrl = "https://raw.githubusercontent.com/$githubUser/$githubRepo/$githubBranch/server/web_secret_collector.py"
$multiSecretUrl = "https://raw.githubusercontent.com/$githubUser/$githubRepo/$githubBranch/server/multi_secret_collector.py"
$updaterUrl = "https://raw.githubusercontent.com/$githubUser/$githubRepo/$githubBranch/server/mcp_config_updater.py"

try {
    Invoke-WebRequest -Uri $serverUrl -OutFile "meta_mcp_server.py" -UseBasicParsing
    Invoke-WebRequest -Uri $mainUrl -OutFile "__main__.py" -UseBasicParsing
    Invoke-WebRequest -Uri $webSecretUrl -OutFile "web_secret_collector.py" -UseBasicParsing
    Invoke-WebRequest -Uri $multiSecretUrl -OutFile "multi_secret_collector.py" -UseBasicParsing
    Invoke-WebRequest -Uri $requirementsUrl -OutFile "requirements.txt" -UseBasicParsing
    Invoke-WebRequest -Uri $pyprojectUrl -OutFile "pyproject.toml" -UseBasicParsing
    Invoke-WebRequest -Uri $updaterUrl -OutFile "mcp_config_updater.py" -UseBasicParsing
} catch {
    Write-Host "❌ Failed to download Install MCP server files." -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# Check if uv is installed
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "📦 Installing uv..." -ForegroundColor Yellow
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
}

# Create __init__.py
New-Item -ItemType File -Name "__init__.py" -Force | Out-Null

# Create local bin directory
$localBin = "$env:USERPROFILE\.local\bin"
New-Item -ItemType Directory -Force -Path $localBin | Out-Null

# Install the mcp-collect-secret tool directly (embedded in this script)
Write-Host "📦 Installing mcp-collect-secret tool..." -ForegroundColor Yellow
$collectSecretContent = @'
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
        
        # Set restrictive permissions (Windows doesn't have chmod)
        # On Windows, files are created with user-only permissions by default
        
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
'@

$collectSecretContent | Out-File -FilePath "$localBin\mcp-collect-secret.py" -Encoding UTF8

# Create a batch file wrapper for mcp-collect-secret
@"
@echo off
python "%USERPROFILE%\.local\bin\mcp-collect-secret.py" %*
"@ | Out-File -FilePath "$localBin\mcp-collect-secret.bat" -Encoding ASCII

# Install the configuration updater
Write-Host "📦 Installing MCP configuration updater..." -ForegroundColor Yellow

# Download and install the Python script
$updaterPyUrl = "https://raw.githubusercontent.com/$githubUser/$githubRepo/$githubBranch/server/mcp_config_updater.py"
Invoke-WebRequest -Uri $updaterPyUrl -OutFile "$localBin\mcp_config_updater.py" -UseBasicParsing

# Create a batch file wrapper for the updater
@"
@echo off
setlocal

REM Find the Python script location
set SCRIPT_NAME=mcp_config_updater.py

if exist "%USERPROFILE%\.local\bin\%SCRIPT_NAME%" (
    set SCRIPT_PATH=%USERPROFILE%\.local\bin\%SCRIPT_NAME%
) else if exist "%USERPROFILE%\mcp-servers\install-mcp\%SCRIPT_NAME%" (
    set SCRIPT_PATH=%USERPROFILE%\mcp-servers\install-mcp\%SCRIPT_NAME%
) else if exist "%USERPROFILE%\mcp-servers\install-mcp\server\%SCRIPT_NAME%" (
    set SCRIPT_PATH=%USERPROFILE%\mcp-servers\install-mcp\server\%SCRIPT_NAME%
) else (
    echo Error: Could not find MCP config updater script.
    echo Expected locations:
    echo   - %USERPROFILE%\.local\bin\%SCRIPT_NAME%
    echo   - %USERPROFILE%\mcp-servers\install-mcp\%SCRIPT_NAME%
    echo   - %USERPROFILE%\mcp-servers\install-mcp\server\%SCRIPT_NAME%
    echo.
    echo Please run the Install MCP installer first.
    exit /b 1
)

python "%SCRIPT_PATH%" %*
"@ | Out-File -FilePath "$localBin\mcp-config-update.bat" -Encoding ASCII

# Add to PATH if not already there
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$localBin*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$localBin", "User")
    $env:Path += ";$localBin"
}

# Update MCP client configurations
Write-Host "⚙️  Configuring MCP clients..." -ForegroundColor Yellow

# Try using the updater first
try {
    python "$localBin\mcp-config-update.py" install-mcp --command uv --args run --python 3.11 --with mcp`>=1.0.0 --with fastmcp`>=0.1.0 "$mcpPath\meta_mcp_server.py"
} catch {
    Write-Host "⚠️  Configuration updater failed, using fallback method..." -ForegroundColor Yellow
    
    # Fallback Python script
    $pythonScript = @'
import json
import os
from pathlib import Path

configs = {
    'claude_code': Path.home() / '.claude.json',
    'claude_desktop': Path.home() / 'AppData/Roaming/Claude/claude_desktop_config.json',
    'cursor': Path.home() / 'AppData/Roaming/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json',
    'windsurf': Path.home() / '.codeium/windsurf/mcp_config.json',
}

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
            'command': 'uv',
            'args': ['run', '--python', '3.11', '--with', 'mcp>=1.0.0', '--with', 'fastmcp>=0.1.0', str(Path.home() / 'mcp-servers/install-mcp/meta_mcp_server.py')]
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
'@

    python -c $pythonScript
}

# Verify mcp-collect-secret was installed
if (Test-Path "$localBin\mcp-collect-secret.bat") {
    Write-Host "✅ mcp-collect-secret tool installed successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️  Warning: mcp-collect-secret tool installation may have failed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✨ Install MCP installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "The following tools are now available:" -ForegroundColor Cyan
Write-Host "  - mcp-config-update: Update MCP client configurations" -ForegroundColor White
Write-Host "  - mcp-collect-secret: Securely collect API keys and secrets" -ForegroundColor White
Write-Host ""
Write-Host "You may need to restart your terminal for PATH changes to take effect." -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Restart your MCP client (Claude Desktop, Cursor, etc.)"
Write-Host "2. Ask your AI: 'Can you test the install-mcp server?'"
Write-Host "3. Then try: 'Install the GitHub MCP server for me'"
Write-Host ""
Write-Host "Documentation: https://github.com/$githubUser/$githubRepo" -ForegroundColor Gray

# Optional: Run test
Write-Host ""
$response = Read-Host "Would you like to test the installation? (y/N)"
if ($response -eq 'y' -or $response -eq 'Y') {
    Write-Host "Running installation test..." -ForegroundColor Yellow
    $testUrl = "https://raw.githubusercontent.com/$githubUser/$githubRepo/$githubBranch/test_meta_mcp.py"
    Invoke-WebRequest -Uri $testUrl -OutFile "test_meta_mcp.py" -UseBasicParsing
    python test_meta_mcp.py
    Remove-Item "test_meta_mcp.py"
}
