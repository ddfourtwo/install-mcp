# Install MCP 🚀

**The simplest way to manage MCP servers through your AI agent**

Install MCP is a meta-MCP server that enables AI agents to install, configure, and manage other MCP servers for you. No more manual JSON editing or complex command-line installations - just ask your AI assistant to handle it.

## 🌟 Key Features

- **Agent-First Design**: Install and manage MCP servers by simply asking your AI
- **Universal Compatibility**: Works with Claude Desktop, Claude Code, Cursor, and Windsurf
- **Centralized Management**: All configurations and secrets stored in one place
- **Secure Secret Handling**: Web-based secure collection for API keys and tokens
- **One-Line Installation**: Get started in seconds with a simple command
- **Export/Import Setups**: Share your MCP configuration with your team

## 📦 Installation

### macOS/Linux
```bash
curl -sSL https://raw.githubusercontent.com/ddfourtwo/install-mcp/main/install.sh | bash
```

### Windows
```powershell
powershell -c "irm https://raw.githubusercontent.com/ddfourtwo/install-mcp/main/install.ps1 | iex"
```

After installation:
1. Restart your MCP client (Claude Desktop, Cursor, etc.)
2. Ask your AI: "Can you test the install-mcp server?"
3. You're ready to install any MCP server!

## 💬 Usage Examples

Once installed, just ask your AI assistant:

### Installing Servers
```
"Install the GitHub MCP server for me"
"Can you set up the Slack MCP server?"
"I need the filesystem MCP server installed"
```

### Managing Configurations
```
"Show me all my installed MCP servers"
"Export my MCP setup so I can share it"
"Configure the GitHub server in all my MCP clients"
```

### Handling Secrets
```
"Collect the API key for the OpenAI server"
"Update the GitHub token for my GitHub MCP server"
```

## 🛠️ How It Works

Install MCP acts as a package manager for MCP servers:

1. **Installation**: Handles git cloning, npm installs, and dependency management
2. **Configuration**: Maintains a central config file that syncs to all MCP clients
3. **Secret Management**: Securely collects and stores API keys in a central .env file
4. **Client Updates**: Automatically updates Claude Desktop, Cursor, and other MCP clients

### Directory Structure
```
~/mcp-servers/
├── install-mcp/          # This meta-server
├── mcp-servers-config.json  # Central configuration
├── .env                  # Central secrets (secure)
├── github/              # Example: GitHub MCP server
├── slack/               # Example: Slack MCP server
└── ...                  # Other installed servers
```

## 🔧 Available AI Commands

Your AI assistant can use these tools:

| Command | Description |
|---------|-------------|
| `list_mcp_servers()` | Show all installed servers and their status |
| `execute_in_mcp_directory()` | Run installation commands |
| `collect_secrets()` | Securely collect API keys via web interface |
| `add_server_to_central_config()` | Add server to central configuration |
| `configure_mcp_clients()` | Apply config to all MCP clients |
| `export_mcp_setup()` | Export complete setup for sharing |

## 📚 Supported Server Types

Install MCP can handle various MCP server types:

### NPM Packages
```
# Servers published to npm
Command: npx -y @organization/package-name@latest
```

### GitHub Repositories (Node.js)
```
# Servers with package.json
1. Clone repository
2. Run npm install
3. Run npm build (if needed)
4. Configure with: node path/to/server.js
```

### GitHub Repositories (Python)
```
# Servers with requirements.txt
1. Clone repository  
2. Run pip install -r requirements.txt
3. Configure with: python3 path/to/server.py
```

### Pre-built Executables
```
# Standalone binaries
Configure with direct path to executable
```

## 🔐 Security

- **Secrets are never exposed** in the AI conversation
- API keys are collected via a local-only web interface
- Secrets are stored with restrictive permissions (0600)
- Each server's secrets are namespaced (e.g., `GITHUB_TOKEN` → `GITHUB_GITHUB_TOKEN`)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/CONTRIBUTING.md) for details.

### Development Setup
```bash
# Clone the repository
git clone https://github.com/ddfourtwo/install-mcp.git
cd install-mcp

# Install dependencies
cd server
pip install -r requirements.txt
```

### Running Tests
```bash
python test_meta_mcp.py
```

## 📋 Troubleshooting

### MCP client not recognizing the server?
- Ensure you've restarted your MCP client after installation
- Check that the install path is correct: `~/mcp-servers/install-mcp/`
- Verify Python 3.11+ is installed: `python3 --version`

### Secrets not working?
- Check the central .env file: `~/mcp-servers/.env`
- Ensure secrets are properly namespaced (e.g., `GITHUB_GITHUB_TOKEN`)
- Verify file permissions: `ls -la ~/mcp-servers/.env` (should be `-rw-------`)

### Can't install a specific server?
- Run `list_mcp_servers()` to check current status
- Ensure you have the required tools (git, npm, python3)
- Check the server's specific requirements in its README

## 🌐 Ecosystem

Install MCP is part of the growing MCP (Model Context Protocol) ecosystem:

- [MCP Specification](https://modelcontextprotocol.io)
- [Awesome MCP Servers](https://github.com/punkpeye/awesome-mcp-servers)
- [Claude Desktop](https://claude.ai/download)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp) framework
- Inspired by the need for simpler MCP server management
- Thanks to all contributors and early adopters

---

**Made with ❤️ for the AI-assisted development community**

*Remember: The best interface for AI tools is natural language. Let your AI assistant handle the complexity!*
